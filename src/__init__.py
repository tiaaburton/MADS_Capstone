import configparser
import json
import os

import requests
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_login import LoginManager, current_user, login_required, login_user
from oauthlib.oauth2 import WebApplicationClient
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.model.institutions_get_request_options import InstitutionsGetRequestOptions
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.products import Products

import src.server
from src.user import User

config = configparser.ConfigParser()
script_dir = os.path.dirname(__file__)
config.read(os.path.join(script_dir, 'config.ini'))
GOOGLE_CLIENT_ID = config['GOOGLE']['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = config['GOOGLE']['GOOGLE_CLIENT_SECRET']
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)


def create_app(test_config=None):
    # create and configure the app

    app = Flask(__name__)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    login_manager = LoginManager()
    # Create the login manager for Google SSO
    login_manager.init_app(app)

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
            response = client.institutions_get(inst_request)
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

        return client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=["openid", "email", "profile"],
        )
        # \
        #     redirect(request_uri)

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

    # db.init_app(app)
    # app.register_blueprint(auth.bp)
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


if __name__ == '__main__':
    app = create_app()
    app.run(port=os.getenv('PORT', 8000), ssl_context="adhoc", debug=True)
