import configparser
import json
import os

import base64
import plaid
import requests
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
from src.server import get_plaid_client, request_institutions


from google.oauth2 import id_token
from google.auth.transport import requests as authrequests

import src.auth as auth
import src.db as db
import src.server as server
import src.analysis.safety_measures as safety
import src.analysis.sentiment_analysis as sentiment
from src.db import init_db_command
from src.user import User

# Dashboard-related libraries
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Data visualization libraries
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
        "width": "22rem",
        "padding": "2rem 1rem",
        "color": "white",
    }

    # the styles for the main content position it to the right of the sidebar and
    # add some padding.
    CONTENT_STYLE = {
        "margin-left": "22rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }

    TABS_STYLES = {"height": "44px",
                   "fontWeight": "bold",
                   "backgroundColor": "#131313"}
    TAB_STYLE = {
        "borderBottom": "1px solid #d6d6d6",
        "padding": "6px",
        "fontWeight": "bold",
        "backgroundColor": "#787878",
    }

    TAB_SELECTED_STYLE = {
        "borderTop": "1px solid #d6d6d6",
        "borderBottom": "1px solid #d6d6d6",
        "backgroundColor": "#119DFF",
        "color": "white",
        "padding": "6px",
    }

    dash_app = dash.Dash(
        __name__,
        title="Market Shopper",
        external_stylesheets=[dbc.themes.SUPERHERO],
        suppress_callback_exceptions=True,
        routes_pathname_prefix="/dash/",
        server=server,
        use_pages=True,
        pages_folder="/pages",
    )

    nav_content = [
        html.Div(
            dbc.NavLink(f"{page['name']}", href=page["relative_path"], active=True, style=TABS_STYLES)
        )
        for page in dash.page_registry.values()
    ]

    # Sidebar implementation
    sidebar = html.Div(
        [
            html.Img(src="/static/images/logo.png", style={"width": "100%"}),
            html.Hr(),
            dbc.Nav(nav_content, vertical=True, pills=True),
        ],
        style=SIDEBAR_STYLE,
    )

    dash_app.layout = html.Div(
        [
            html.Div(children=[sidebar], style={"flex": 0.35}),
            html.Div(children=[dash.page_container], style={"flex": 1}),
        ],
        style={"display": "flex", "flex-direction": "row"},
    )

    return dash_app


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, static_folder="static")
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    # Initialize Dash dashboard built in market shopper (change naming and location)

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
        config["PLAID"]["PLAID_CLIENT_ID"] = request.form["client_id"]
        config["PLAID"]["PLAID_SECRET"] = request.form["secret_key"]
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

    @app.route("/login")
    def login():

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

        return render_template("auth/login.html")

    @app.route("/login/callback", methods=["POST"])
    def callback():
        if request.method == "POST":
            PLAID_CLIENT_ID = config["PLAID"]["PLAID_CLIENT_ID"]
            PLAID_SECRET = config["PLAID"]["PLAID_SECRET"]
            PLAID_ENV = config["PLAID"]["PLAID_ENV"]
            session["PLAID_CLIENT_ID"] = PLAID_CLIENT_ID
            session["PLAID_SECRET"] = PLAID_SECRET

            csrf_token_cookie = request.cookies.get("g_csrf_token")
            token = request.form.get("credential")
            if not csrf_token_cookie:
                raise Exception("No CSRF token in Cookie.")
                # webapp2.abort(400, 'No CSRF token in Cookie.')
            # csrf_token_body = request.get('g_csrf_token')
            csrf_token_body = request.form.get("g_csrf_token")
            if not csrf_token_body:
                #     webapp2.abort(400, 'No CSRF token in post body.')
                raise Exception("No CSRF token in Body.")
            if csrf_token_cookie != csrf_token_body:
                #     webapp2.abort(400, 'Failed to verify double submit cookie.')
                raise Exception("Failed to verify double submit cookie.")

            try:
                # Specify the CLIENT_ID of the app that accesses the backend:
                idinfo = id_token.verify_oauth2_token(
                    token, authrequests.Request(), GOOGLE_CLIENT_ID
                )

                # # ID token is valid. Get the user's Google Account ID from the decoded token.
                unique_id = idinfo["sub"]
                users_name = idinfo["name"]
                users_email = idinfo["email"]
                picture = idinfo["picture"]
            except ValueError as e:
                # Invalid token
                raise Exception("Error: " + str(e))
                # raise Exception("Invalid Google OAuth token: " + str(token))

            user = User(
                id_=unique_id, name=users_name, email=users_email, profile_pic=picture
            )

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

    @app.route("/<path:filename>")
    def send_file(filename):
        return send_from_directory(app.static_folder, filename)

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(server.bp)
    app.register_blueprint(sentiment.bp)

    # OAuth 2 client setup
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
    dash_app = create_dashboard(app)
    return dash_app.server


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    os.environ["FLASK_ENV"] = "development"
    app = create_app()
    app.run(port=os.getenv("PORT", 8080), ssl_context="adhoc", debug=True)
