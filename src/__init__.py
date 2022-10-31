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

    ######################
    ### BEGIN APP LAYOUT #
    ######################

    dash_app = dash.Dash(__name__
                         , external_stylesheets=[dbc.themes.SUPERHERO]
                         , suppress_callback_exceptions=True
                         , routes_pathname_prefix="/dash/"
                         , server=server
                         , use_pages=True
                         , pages_folder="/templates/pages")

    dash_app.title = "Market Shopper"

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

    # # S&P 500 Analytics main page
    # spx_main_page = html.Div(children=[
    #     html.Br(),
    #     html.Div(children=[
    #         html.H2('Portfolio'),
    #         html.Hr(),
    #         html.Div(children=[
    #             dcc.Tabs(children=[
    #                 dcc.Tab(id='spx-ml-tab', label='ML/DL Analysis', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='spx-vol-tab', label='Volatility Markets', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE, children=[
    #                         html.P(),
    #                         dbc.Row(children=[
    #                             html.P(),
    #                             dbc.Col(children=[
    #                                 dcc.RadioItems(id='sp-vol-radio', value='2',
    #                                                options=[{'label': i, 'value': j} for i, j in
    #                                                         [('1m', '.0833'), ('6m', '.5'),
    #                                                          ('1y', '1'), ('2y', '2'),
    #                                                          ('5y', '5'), ('Max', 'Max')]],
    #                                                style={'marginLeft': '500px'},
    #                                                labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
    #                         ]),
    #                         html.P(),
    #                         dbc.Row(children=[
    #                             dbc.Col(dcc.Graph(id='sp-vix-vol-graph')),
    #                             dbc.Col(dcc.Graph(id='sp-vvix-vix-graph')),
    #                         ]),
    #
    #                         dbc.Row(children=[
    #                             dbc.Col(dcc.Graph(id='sp-vix-skew-graph')),
    #                             dbc.Col(dcc.Graph(id='sp-vix-vxn-graph'))
    #                         ]),
    #                     ]),
    #                 dcc.Tab(id='spx-corr-tab', label='Correlations', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
    #                         children=[
    #                             html.P(),
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.RadioItems(id='sp-corr-radio', value='2',
    #                                                    options=[{'label': i, 'value': j} for i, j in
    #                                                             [('1m', '.0833'), ('6m', '.5'),
    #                                                              ('1y', '1'), ('2y', '2'),
    #                                                              ('5y', '5'), ('Max', 'Max')]],
    #                                                    style={'marginLeft': '500px'},
    #                                                    labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
    #                             ]),
    #                             html.P(),
    #                             dbc.Row(children=[
    #                                 dbc.Col(dcc.Graph(id='sp-corr-20d-graph')),
    #                                 dbc.Col(dcc.Graph(id='sp-corr-20d-change'))
    #                             ])
    #                         ]),
    #                 dcc.Tab(id='spx-tech-tab', label='Technicals', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
    #                         children=[
    #                             html.P(),
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.RadioItems(id='sp-tech-radio', value='2',
    #                                                    options=[{'label': i, 'value': j} for i, j in
    #                                                             [('1m', '.0833'), ('6m', '.5'),
    #                                                              ('1y', '1'), ('2y', '2'),
    #                                                              ('5y', '5'), ('Max', 'Max')]],
    #                                                    style={'marginLeft': '500px'},
    #                                                    labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
    #                             ]),
    #                             html.P(),
    #                             dbc.Row(children=[
    #                                 dbc.Col(dcc.Graph(id='sp-tech-rsi-graph')),
    #                                 dbc.Col(dcc.Graph(id='sp-tech-sma-graph'))
    #                             ])
    #                         ])
    #             ], style=TABS_STYLES)
    #         ])
    #     ])
    # ])
    #
    # # Nasdaq 100 Analytics main page
    # qqq_main_page = html.Div(children=[
    #     html.Br(),
    #     html.Div(children=[
    #         html.H2('Nasdaq 100 Analytics'),
    #         html.Hr(),
    #         html.Div(children=[
    #             dcc.Tabs(children=[
    #                 dcc.Tab(id='qqq-ml-tab', label='ML/DL Analysis', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='qqq-vol-tab', label='Volatility Markets', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='qqq-corr-tab', label='Correlations', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='qqq-tech-tab', label='Technicals', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE)
    #             ], style=TABS_STYLES)
    #         ])
    #     ])
    # ])
    #
    # # Russell 2000 Analytics main page
    # r2k_main_page = html.Div(children=[
    #     html.Br(),
    #     html.Div(children=[
    #         html.H2('Russell 2000 Analytics'),
    #         html.Hr(),
    #         html.Div(children=[
    #             dcc.Tabs(children=[
    #                 dcc.Tab(id='r2k-ml-tab', label='ML/DL Analysis', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='r2k-vol-tab', label='Volatility Markets', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='r2k-corr-tab', label='Correlations', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='r2k-tech-tab', label='Technicals', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE)
    #             ], style=TABS_STYLES)
    #         ])
    #     ])
    # ])
    #
    # # Credit Market Analytics main page
    # credit_main_page = html.Div(children=[
    #     html.Br(),
    #     html.Div(children=[
    #         html.H2('Credit Market Analytics'),
    #         html.Hr(),
    #         html.Div(children=[
    #             dcc.Tabs(children=[
    #                 dcc.Tab(id='credit-treas-tab', label='Treasury Markets', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE, children=[
    #                         html.Div(children=[
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.RadioItems(id='credit-treas-radio', value='2',
    #                                                    options=[{'label': i, 'value': j} for i, j in
    #                                                             [('1m', '.0833'), ('6m', '.5'),
    #                                                              ('1y', '1'), ('2y', '2'),
    #                                                              ('5y', '5'), ('Max', 'Max')]],
    #                                                    style={'marginLeft': '150px'},
    #                                                    labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
    #                                 dbc.Col(children=[
    #                                     dcc.Checklist(id='credit-treas-indices', value=['SPX'],
    #                                                   options=[{'label': x, 'value': y}
    #                                                            for x, y in [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
    #                                                   style={'marginLeft': '250px'},
    #                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-2yr-graph')]),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-5yr-graph')])]),
    #
    #                             html.Hr(),
    #
    #                             dbc.Row(children=[
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-10yr-graph')]),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-30yr-graph')])]),
    #
    #                             html.Hr(),
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-5yrreal-graph')]),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-10yrreal-graph')])])])]),
    #
    #                 dcc.Tab(id='credit-curves-tab', label='Treasury Curves', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE, children=[
    #                         html.Div(children=[
    #                             dbc.Row(children=[
    #
    #                                 dbc.Row(children=[
    #                                     html.P(),
    #                                     dbc.Col(children=[
    #                                         dcc.RadioItems(id='credit-curve-radio', value='2',
    #                                                        options=[{'label': i, 'value': j} for i, j in
    #                                                                 [('1m', '.0833'), ('6m', '.5'),
    #                                                                  ('1y', '1'), ('2y', '2'),
    #                                                                  ('5y', '5'), ('Max', 'Max')]],
    #                                                        style={'marginLeft': '150px'},
    #                                                        labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
    #                                     dbc.Col(children=[
    #                                         dcc.Checklist(id='credit-curve-indices', value=['SPX'],
    #                                                       options=[{'label': x, 'value': y}
    #                                                                for x, y in
    #                                                                [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
    #                                                       style={'marginLeft': '250px'},
    #                                                       labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),
    #
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-curve-2s10s')]),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-curve-2s30s')])]),
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-curve-5s10s')]),
    #
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-curve-10s30s')])])])]),
    #
    #                 dcc.Tab(id='credit-corp-tab', label='Corporate Credit Markets', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE, children=[
    #                         html.Div(children=[
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.RadioItems(id='credit-corp-radio', value='2',
    #                                                    options=[{'label': i, 'value': j} for i, j in
    #                                                             [('1m', '.0833'), ('6m', '.5'),
    #                                                              ('1y', '1'), ('2y', '2'),
    #                                                              ('5y', '5'), ('Max', 'Max')]],
    #                                                    style={'marginLeft': '150px'},
    #                                                    labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
    #                                 dbc.Col(children=[
    #                                     dcc.Checklist(id='credit-corp-indices', value=['SPX'],
    #                                                   options=[{'label': x, 'value': y}
    #                                                            for x, y in [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
    #                                                   style={'marginLeft': '250px'},
    #                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='credit-corp-rates-graph')]),
    #
    #                                 html.Hr(),
    #                                 html.P(),
    #                                 dbc.Row(children=[
    #                                     dbc.Col(children=[
    #                                         dcc.Graph(id='HY-minus-A-graph')]),
    #                                     dbc.Col(children=[
    #                                         dcc.Graph(id='BBB-minus-A-graph')])]),
    #
    #                                 html.Hr(),
    #
    #                                 dbc.Row(children=[
    #                                     html.P(),
    #                                     dbc.Col(children=[
    #                                         dcc.Graph('BB-minus-BBB-graph')]),
    #                                     dbc.Col(children=[
    #                                         dcc.Graph('CCC-minus-BB-graph')])])])])]),
    #
    #                 dcc.Tab(id='credit-addl-tab', label='Additional Metrics', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #             ], style=TABS_STYLES)
    #         ])
    #     ])
    # ])
    #
    # # Econ Data main page
    # econ_main_page = html.Div(children=[
    #     html.Br(),
    #     html.Div(children=[
    #         html.H2('Economic Data & Analytics'),
    #         html.Hr(),
    #         html.Div(children=[
    #             dcc.Tabs(children=[
    #                 dcc.Tab(id='econ-emp-tab', label='Employment Indicators', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE, children=[
    #                         html.Div(children=[
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.RadioItems(id='econ-emp-radio', value='2',
    #                                                    options=[{'label': i, 'value': j} for i, j in
    #                                                             [('1m', '.0833'), ('6m', '.5'),
    #                                                              ('1y', '1'), ('2y', '2'),
    #                                                              ('5y', '5'), ('Max', 'Max')]],
    #                                                    style={'marginLeft': '150px'},
    #                                                    labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
    #                                 dbc.Col(children=[
    #                                     dcc.Checklist(id='econ-emp-indices', value=['SPX'],
    #                                                   options=[{'label': x, 'value': y}
    #                                                            for x, y in [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
    #                                                   style={'marginLeft': '250px'},
    #                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),
    #
    #                             dbc.Row(children=[
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='econ-emp-nonfarm-graph')]),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph(id='econ-emp-claims-graph')])]),
    #
    #                             html.Hr(),
    #
    #                             dbc.Row(children=[
    #                                 html.P(),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph('econ-emp-labor-graph')]),
    #                                 dbc.Col(children=[
    #                                     dcc.Graph('econ-emp-unemp-graph')])])])]),
    #
    #                 dcc.Tab(id='econ-inflation-tab', label='Inflation Indicators', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='econ-activity-tab', label='Activity Indicators', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #                 dcc.Tab(id='eocn-housing-tab', label='Housing Indicators', style=TAB_STYLE,
    #                         selected_style=TAB_SELECTED_STYLE),
    #             ], style=TABS_STYLES)
    #         ])
    #     ])
    # ])
    #
    content = html.Div(id="page-content", style=CONTENT_STYLE)

    dash_app.layout = html.Div([dcc.Location(id="url"), sidebar, content])
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

    @app.route("/account/")
    def account():
        return "The account page"

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

    @app.route("/discovery")
    def discovery():
        return "The discovery page"

    @app.route("/predictions")
    def predictions():
        return "The prediction page"

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
