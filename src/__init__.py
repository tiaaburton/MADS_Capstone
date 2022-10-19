import json
import os

from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import redirect
from flask import url_for
import plaid
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.model.institutions_get_request_options import InstitutionsGetRequestOptions
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.products import Products


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

    from dotenv import load_dotenv

    load_dotenv()

    # Fill in your Plaid API keys - https://dashboard.plaid.com/account/keys
    PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
    PLAID_SECRET = os.getenv('PLAID_SECRET')
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
        if 'username' in session:
            # If a user is logged in, we want to provide them with options
            # to log into a certain portfolio to test.
            request = InstitutionsGetRequest(
                country_codes=[CountryCode('US')],
                count=500,
                offset=0,
                options=InstitutionsGetRequestOptions(products=[Products('investments')])
            )
            response = client.institutions_get(request)
            # With the institutions' response, we can capture the names
            # to display on the front end for our application.
            institutions = [inst['name'] for inst in response['institutions']]
            institutions.sort()
            # Lastly, we pass the institution names to the credential template
            return render_template('profile/manager.html', institutions=institutions)
        else:
            # We want to redirect users to login if we don't
            # have a session for the user.
            return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        return render_template('auth/login.html')

    @app.route('/logout')
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

    from . import (
        db, auth, server
    )
    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(server.bp)

    return app
