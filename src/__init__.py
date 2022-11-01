import configparser
import json
import os
from pathlib import Path

import plaid
import requests
import datetime as dt
import pandas as pd
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.model.institutions_get_request_options import InstitutionsGetRequestOptions
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.products import Products
from src.server import get_plaid_client, request_institutions

import src.auth
import src.db
import src.server
import src.analysis.safety_measures as safety
import src.analysis.sentiment_analysis as sentiment
from src.db import init_db_command
from src.user import User

# Dashboard-related libraries
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
# import dash_auth


# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import flask

config = configparser.ConfigParser()
script_dir = os.path.dirname(__file__)
config.read(os.path.join(script_dir, "config.ini"))
GOOGLE_CLIENT_ID = config["GOOGLE"]["GOOGLE_CLIENT_ID"]
PLAID_ENV = config["PLAID"]["PLAID_ENV"]
GOOGLE_CLIENT_SECRET = config["GOOGLE"]["GOOGLE_CLIENT_SECRET"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


def create_dashboard(server: flask.Flask):
    # the style arguments for the sidebar. We use position:fixed and a fixed width
    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "22rem",
        "padding": "2rem 1rem",
        # "background-color": "#f8f9fa",
        "color": "white"
    }

    # the styles for the main content position it to the right of the sidebar and
    # add some padding.
    CONTENT_STYLE = {
        "margin-left": "22rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }

    TABS_STYLES = {
        'height': '44px'
    }
    TAB_STYLE = {
        'borderBottom': '1px solid #d6d6d6',
        'padding': '6px',
        'fontWeight': 'bold',
        'backgroundColor': '#787878'
    }

    TAB_SELECTED_STYLE = {
        'borderTop': '1px solid #d6d6d6',
        'borderBottom': '1px solid #d6d6d6',
        'backgroundColor': '#119DFF',
        'color': 'white',
        'padding': '6px'
    }

    dash_app = dash.Dash(__name__
                         , title="Market Shopper"
                         , external_stylesheets=[dbc.themes.SUPERHERO]
                         , suppress_callback_exceptions=True
                         , routes_pathname_prefix="/dash/"
                         , server=server
                         , use_pages=True
                         , pages_folder="/templates/pages")

    nav_content = [
        dbc.NavLink("Home", href="/home", active="exact"),
        dbc.NavLink("Portfolio", href="/spx-main", active="exact"),
        dbc.NavLink("Equity Market Analytics", href="/qqq-main", active="exact"),
        dbc.NavLink("Bond Analytics", href="/r2k-main", active="exact"),
        dbc.NavLink("Economic Data", href="/crypto-main", active="exact"),
        dbc.NavLink("Market Signal Analysis", href="/credit-main", active="exact")
    ]
    # Sidebar implementation
    sidebar = html.Div([
        html.H2("DashBoard", className="display-4"),
        html.Hr(),
        dbc.Nav(nav_content, vertical=True, pills=True)
    ], style=SIDEBAR_STYLE)

    content = html.Div(id="page-content", style=CONTENT_STYLE)

    dash_app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

    # Callback to control render of pages given sidebar navigation
    @dash_app.callback(Output("page-content", "children"),
                  [Input("url", "pathname")])
    def render_page_content(pathname):
        from src.templates.pages import analysis, discovery, home, prediction

        if pathname == "/home":
            return home.layout
        elif pathname == "/analysis":
            return analysis.layout
        elif pathname == "/discovery":
            return discovery.layout
        elif pathname == "/predictions":
            return prediction.layout

        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )

    return dash_app


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    # Initialize Dash dashboard built in market shopper (change naming and location)
    create_dashboard(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    host = plaid.Environment.Sandbox

    if PLAID_ENV == "sandbox":
        host = plaid.Environment.Sandbox

    if PLAID_ENV == "development":
        host = plaid.Environment.Development

    if PLAID_ENV == "production":
        host = plaid.Environment.Production

    # Create the login manager for Google SSO
    login_manager = LoginManager()
    login_manager.init_app(app)

    # Flask-Login helper to retrieve a user from our db
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    def get_google_provider_cfg():
        return requests.get(GOOGLE_DISCOVERY_URL).json()

    @app.route("/plaid_credential_store", methods=["POST"])
    def store_plaid_credentials():
        session["PLAID_CLIENT_ID"] = request.form["client_id"]
        session["PLAID_SECRET"] = request.form["secret_key"]
        return redirect(url_for("index"))

    # Architected by Market Shoppers
    @app.route("/")
    def index():
        if current_user.is_authenticated and "PLAID_SECRET" in session:
            # Retrieve the institutions that have test investments accounts
            institutions = request_institutions()
            # Pass the institution names to the credential template for user selection
            return render_template("profile/manager.html", institutions=institutions)
        elif current_user.is_authenticated and "PLAID_SECRET" not in session:
            # Allow users to provide Plaid credentials when logged into the app
            return render_template("profile/manager.html")
        else:
            # Redirect users to login if there isn't a user in session
            return redirect(url_for("login"))

    # @app.route('/login', methods=['GET', 'POST'])
    @app.route("/login")
    def login():
        # if request.method == 'POST':
        #     session['username'] = request.form['username']
        #     return redirect(url_for('index'))
        # return render_template('auth/login.html')

        ### Google SSO Code ###
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=f"{request.base_url}/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)

    @app.route("/login/callback")
    def callback():
        # Get authorization code Google sent back to you
        code = request.args.get("code")
        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code,
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens!
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Save the token to help log out
        session["state"] = client.state

        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # You want to make sure their email is verified.
        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            picture = userinfo_response.json()["picture"]
            users_name = userinfo_response.json()["given_name"]
        else:
            return "User email not available or not verified by Google.", 400

        # Create a user in your db with the information provided
        # by Google
        user = User(
            id_=unique_id, name=users_name, email=users_email, profile_pic=picture
        )

        # Doesn't exist? Add it to the database.
        if not User.get(unique_id):
            User.create(unique_id, users_name, users_email, picture)

        # Begin user session by logging the user in
        login_user(user)

        # Send user to portfolio manager to start using entering credentials to unlock
        # a feature within the app
        return redirect(url_for("index"))

    @app.route("/logout")
    @login_required
    def logout():
        # remove the username from the session if it's there
        session.clear()
        logout_user()
        return redirect(url_for("index"))

    @app.route("/portfolio", methods=["GET", "POST"])
    def analysis():
        # paths = {}
        # for i in range(len(Path(__file__).parents)):
        #     paths[i] = str(Path(__file__).parents[i])
        # return paths
        p_str = f'{str(Path(__file__).parents[3])}/Downloads/test_portfolio2.csv'
        start = dt.datetime(2022, 1, 1).date()
        end = dt.datetime.today().date()
        p = safety.calculate_VaR(safety.test_portfolio('pandas', p_str), start_date=start, end_date=end)

        var_chart = safety.VaR_Chart()
        var_chart.labels.grouped = [int(day) for day in p.Day.values]
        var_chart.data.data = [float(val) for val in p.VaR.values]

        ChartJSON = var_chart.get()

        return render_template('pages/analysis.html',
                               context={"chartJSON": ChartJSON})
        # return "This is the analysis page."

    def return_portfolio(holdings, securities):
        from collections import defaultdict

        portfolio = defaultdict(dict)
        for sec in securities:
            if sec["df_type"] != "derivative":
                sec_ticker = sec["ticker_symbol"]
                sec_quant = [
                    holding["quantity"]
                    for holding in holdings
                    if (holding["security_id"] == sec["security_id"])
                ]
                sec_value = [
                    holding["institution_value"]
                    for holding in holdings
                    if (holding["security_id"] == sec["security_id"])
                ]

                # Some checks in place to ensure
                if sec_ticker is not None and ":" in sec_ticker:
                    sec_ticker = sec_ticker.split(":")[-1]

                portfolio[sec_ticker]["name"] = sec_ticker
                portfolio[sec_ticker]["df_type"] = sec["df_type"]
                if sec_quant is not None and len(sec_quant) > 0:
                    portfolio[sec_ticker]["quantity"] = sec_quant[0]
                if sec_value is not None and len(sec_value) > 0:
                    portfolio[sec_ticker]["value"] = sec_value[0]

        return json.dumps(portfolio)

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(server.bp)
    app.register_blueprint(sentiment.bp)

    # OAuth 2 client setup
    client = WebApplicationClient(GOOGLE_CLIENT_ID)

    return app


if __name__ == "__main__":
    app = create_app()
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.run(port=os.getenv("PORT", 8080), ssl_context="adhoc", debug=True)
