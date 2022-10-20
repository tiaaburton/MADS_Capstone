import json
import os
import sqlite3
import requests
from oauthlib.oauth2 import WebApplicationClient
import configparser

from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
import plaid
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.model.institutions_get_request_options import InstitutionsGetRequestOptions
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.products import Products

from db import init_db_command
from user import User
import db, auth, server

config = configparser.ConfigParser()
script_dir = os.path.dirname(__file__)
config.read(os.path.join(script_dir, 'config.ini'))
GOOGLE_CLIENT_ID = config['GOOGLE']['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = config['GOOGLE']['GOOGLE_CLIENT_SECRET']
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

login_manager = LoginManager()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Create the login manager for Google SSO
    login_manager.init_app(app)

    from dotenv import load_dotenv

    load_dotenv()

    # Fill in your Plaid API keys - https://dashboard.plaid.com/account/keys
    PLAID_CLIENT_ID = config['PLAID']['PLAID_CLIENT_ID']
    PLAID_SECRET = config['PLAID']['PLAID_CLIENT_ID']
    # PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
    # PLAID_SECRET = os.getenv('PLAID_SECRET')
    # Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
    # password: pass_good)
    # Use `development` to test with live users and credentials and `production`
    # to go live
    PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')
    # PLAID_PRODUCTS is a comma-separated list of products to use when initializing
    # Link. Note that this list must contain 'assets' in order for the app to be
    # able to create and retrieve asset reports.
    PLAID_PRODUCTS = os.getenv('PLAID_PRODUCTS', 'transactions').split(',')

    # PLAID_COUNTRY_CODES is a comma-separated list of countries for which users
    # will be able to select institutions from.
    PLAID_COUNTRY_CODES = os.getenv('PLAID_COUNTRY_CODES', 'US').split(',')

    def empty_to_none(field):
        value = os.getenv(field)
        if value is None or len(value) == 0:
            return None
        return value

    host = plaid.Environment.Sandbox

    if PLAID_ENV == 'sandbox':
        host = plaid.Environment.Sandbox

    if PLAID_ENV == 'development':
        host = plaid.Environment.Development

    if PLAID_ENV == 'production':
        host = plaid.Environment.Production

    # Parameters used for the OAuth redirect Link flow.
    #
    # Set PLAID_REDIRECT_URI to 'http://localhost:3000/'
    # The OAuth redirect flow requires an endpoint on the developer's website
    # that the bank website should redirect to. You will need to configure
    # this redirect URI for your client ID through the Plaid developer dashboard
    # at https://dashboard.plaid.com/team/api.
    PLAID_REDIRECT_URI = empty_to_none('PLAID_REDIRECT_URI')

    configuration = plaid.Configuration(
        host=host,
        api_key={
            'clientId': PLAID_CLIENT_ID,
            'secret': PLAID_SECRET,
            'plaidVersion': '2020-09-14'
        }
    )

    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    products = []
    for product in PLAID_PRODUCTS:
        products.append(Products(product))

    # We store the access_token in memory - in production, store it in a secure
    # persistent data store.
    access_token = None
    # The payment_id is only relevant for the UK Payment Initiation product.
    # We store the payment_id in memory - in production, store it in a secure
    # persistent data store.
    payment_id = None
    # The transfer_id is only relevant for Transfer ACH product.
    # We store the transfer_id in memomory - in produciton, store it in a secure
    # persistent data store
    transfer_id = None

    item_id = None

    # @bp.route('/api/info', methods=['POST'])
    # def info():
    #     global access_token
    #     global item_id
    #     return jsonify({
    #         'item_id': item_id,
    #         'access_token': access_token,
    #         'products': PLAID_PRODUCTS
    #     })

    # Architected by Market Shoppers
    @app.route('/')
    def index():
        # if 'username' in session:
        if current_user.is_authenticated:
            # If a user is logged in, we want to provide them with options
            # to log into a certain portfolio to test.
            inst_request = InstitutionsGetRequest(
                country_codes=[CountryCode('US')],
                count=500,
                offset=0,
                options=InstitutionsGetRequestOptions(products=[Products('investments')])
            )
            # response = client.institutions_get(inst_request)
            # # With the institutions' response, we can capture the names
            # # to display on the front end for our application.
            # institutions = [inst['name'] for inst in response['institutions']]
            # institutions.sort()
            institutions = ["Vanguard", "Fidelity", "Other Examples"]
            # Lastly, we pass the institution names to the credential template
            return render_template('profile/manager.html', institutions=institutions)
        else:
            # We want to redirect users to login if we don't
            # have a session for the user.
            return redirect(url_for('login'))

    # @app.route('/login', methods=['GET', 'POST'])
    @app.route('/login')
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
            redirect_uri=request.base_url + "/callback",
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
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens!
        client.parse_request_body_response(json.dumps(token_response.json()))

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

        # Send user back to homepage
        return redirect(url_for("index"))

    @app.route('/logout')
    @login_required
    def logout():
        # remove the username from the session if it's there
        session.pop('username', None)
        return redirect(url_for('index'))

    @app.route('/account/')
    def account():
        return 'The account page'

    @app.route('/portfolio', methods=['GET', 'POST'])
    def analysis():
        # Pull Holdings for an Item
        inv_request = InvestmentsHoldingsGetRequest(access_token=session['access_token'])
        response = client.investments_holdings_get(inv_request)
        # Handle Holdings response
        holdings = response['holdings']
        # Handle Securities response
        securities = response['securities']
        return return_portfolio(holdings, securities)

    def return_portfolio(holdings, securities):
        from collections import defaultdict
        portfolio = defaultdict(dict)
        for sec in securities:
            if sec['type'] != 'derivative':
                sec_ticker = sec['ticker_symbol']
                sec_quant = [holding['quantity'] for holding in holdings
                             if (holding['security_id'] == sec['security_id'])]
                sec_value = [holding['institution_value'] for holding in holdings
                             if (holding['security_id'] == sec['security_id'])]

                # Some checks in place to ensure
                if sec_ticker is not None and ':' in sec_ticker:
                    sec_ticker = sec_ticker.split(':')[-1]

                portfolio[sec_ticker]['name'] = sec_ticker
                portfolio[sec_ticker]['type'] = sec['type']
                if sec_quant is not None and len(sec_quant) > 0:
                    portfolio[sec_ticker]['quantity'] = sec_quant[0]
                if sec_value is not None and len(sec_value) > 0:
                    portfolio[sec_ticker]['value'] = sec_value[0]
        return json.dumps(portfolio)

    @app.route('/discovery')
    def discovery():
        return 'The discovery page'

    @app.route('/predictions')
    def predictions():
        return 'The prediction page'

    db.init_app(app)
    # Naive database setup
    # try:
    #     init_db_command()
    # except sqlite3.OperationalError:
    #     # Assume it's already been created
    #     pass
    app.register_blueprint(auth.bp)
    app.register_blueprint(server.bp)

    # OAuth 2 client setup
    client = WebApplicationClient(GOOGLE_CLIENT_ID)

    return app

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

app = create_app()

if __name__ == '__main__':
    app.run(port=os.getenv('PORT', 8000), ssl_context="adhoc", debug=True)
# create_app()