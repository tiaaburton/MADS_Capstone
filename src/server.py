# source ../PycharmProjects/pythonProject/venv/bin/activate
# Read env vars from .env file
import base64
import datetime
import json
import os
import time
from datetime import datetime
from datetime import timedelta

import pandas as pd
import plaid
from dotenv import load_dotenv
from flask import Blueprint
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from flask import session
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.ach_class import ACHClass
from plaid.model.asset_report_create_request import AssetReportCreateRequest
from plaid.model.asset_report_create_request_options import (
    AssetReportCreateRequestOptions,
)
from plaid.model.asset_report_get_request import AssetReportGetRequest
from plaid.model.asset_report_pdf_get_request import AssetReportPDFGetRequest
from plaid.model.asset_report_user import AssetReportUser
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.identity_get_request import IdentityGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.institutions_get_request import InstitutionsGetRequest
from plaid.model.institutions_get_request_options import InstitutionsGetRequestOptions
from plaid.model.institutions_search_request import InstitutionsSearchRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.investments_transactions_get_request import (
    InvestmentsTransactionsGetRequest,
)
from plaid.model.investments_transactions_get_request_options import (
    InvestmentsTransactionsGetRequestOptions,
)
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_payment_initiation import (
    LinkTokenCreateRequestPaymentInitiation,
)
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.payment_amount import PaymentAmount
from plaid.model.payment_amount_currency import PaymentAmountCurrency
from plaid.model.payment_initiation_address import PaymentInitiationAddress
from plaid.model.payment_initiation_payment_create_request import (
    PaymentInitiationPaymentCreateRequest,
)
from plaid.model.payment_initiation_payment_get_request import (
    PaymentInitiationPaymentGetRequest,
)
from plaid.model.payment_initiation_recipient_create_request import (
    PaymentInitiationRecipientCreateRequest,
)
from plaid.model.products import Products
from plaid.model.recipient_bacs_nullable import RecipientBACSNullable
from plaid.model.sandbox_public_token_create_request import (
    SandboxPublicTokenCreateRequest,
)
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transfer_authorization_create_request import (
    TransferAuthorizationCreateRequest,
)
from plaid.model.transfer_create_idempotency_key import TransferCreateIdempotencyKey
from plaid.model.transfer_create_request import TransferCreateRequest
from plaid.model.transfer_get_request import TransferGetRequest
from plaid.model.transfer_network import TransferNetwork
from plaid.model.transfer_type import TransferType
from plaid.model.transfer_user_address_in_request import TransferUserAddressInRequest
from plaid.model.transfer_user_in_request import TransferUserInRequest

load_dotenv()

app = Flask(__name__)

bp = Blueprint("plaid", __name__, url_prefix="/plaid")

# Fill in your Plaid API keys - https://dashboard.plaid.com/account/keys
# Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
# password: pass_good)
# Use `development` to test with live users and credentials and `production`
# to go live
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
# PLAID_PRODUCTS is a comma-separated list of products to use when initializing
# Link. Note that this list must contain 'assets' in order for the app to be
# able to create and retrieve asset reports.
PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")

# PLAID_COUNTRY_CODES is a comma-separated list of countries for which users
# will be able to select institutions from.
PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")


def empty_to_none(field):
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value


host = plaid.Environment.Sandbox

if PLAID_ENV == "sandbox":
    host = plaid.Environment.Sandbox

if PLAID_ENV == "development":
    host = plaid.Environment.Development

if PLAID_ENV == "production":
    host = plaid.Environment.Production

# Parameters used for the OAuth redirect Link flow.
#
# Set PLAID_REDIRECT_URI to 'http://localhost:3000/'
# The OAuth redirect flow requires an endpoint on the developer's website
# that the bank website should redirect to. You will need to configure
# this redirect URI for your client ID through the Plaid developer dashboard
# at https://dashboard.plaid.com/team/api.
PLAID_REDIRECT_URI = empty_to_none("PLAID_REDIRECT_URI")

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


def get_plaid_client():
    configuration = plaid.Configuration(
        host=host,
        api_key={
            "clientId": session["PLAID_CLIENT_ID"],
            "secret": session["PLAID_SECRET"],
            "plaidVersion": "2020-09-14",
        },
    )

    api_client = plaid.ApiClient(configuration)
    plaid_client = plaid_api.PlaidApi(api_client)
    return plaid_client


@bp.route("/api/create_link_token", methods=["POST"])
def create_link_token():
    try:
        request = LinkTokenCreateRequest(
            products=products,
            client_name="Market Shopper",
            country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
            language="en",
            # user=LinkTokenCreateRequestUser(
            #     client_user_id=str(time.time())
            # )
        )
        if PLAID_REDIRECT_URI != None:
            request["redirect_uri"] = PLAID_REDIRECT_URI
        # create link token
        response = client.link_token_create(request)
        return jsonify(response.to_dict())
    except plaid.ApiException as e:
        return json.loads(e.body)


# Exchange token flow - exchange a Link public_token for
# an API access_token
# https://plaid.com/docs/#exchange-token-flow


@bp.route("/api/set_access_token", methods=["POST"])
def get_access_token():
    global access_token
    global item_id
    global transfer_id
    public_token = request.form["public_token"]
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response["access_token"]
        item_id = exchange_response["item_id"]
        if "transfer" in PLAID_PRODUCTS:
            transfer_id = authorize_and_create_transfer(access_token)
        return jsonify(exchange_response.to_dict())
    except plaid.ApiException as e:
        return json.loads(e.body)


# Retrieve ACH or ETF account numbers for an Item
# https://plaid.com/docs/#auth


@bp.route("/api/auth", methods=["GET"])
def get_auth():
    try:
        request = AuthGetRequest(access_token=access_token)
        response = client.auth_get(request)
        pretty_print_response(response.to_dict())
        return jsonify(response.to_dict())
    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)


# Retrieve Transactions for an Item
# https://plaid.com/docs/#transactions


@bp.route("/api/transactions", methods=["GET"])
def get_transactions():
    # Set cursor to empty to receive all historical updates
    cursor = ""

    # New transaction updates since "cursor"
    added = []
    modified = []
    removed = []  # Removed transaction ids
    has_more = True
    try:
        # Iterate through each page of new transaction updates for item
        while has_more:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
            )
            response = client.transactions_sync(request).to_dict()
            # Add this page of results
            added.extend(response["added"])
            modified.extend(response["modified"])
            removed.extend(response["removed"])
            has_more = response["has_more"]
            # Update cursor to the next cursor
            cursor = response["next_cursor"]
            pretty_print_response(response)

        # Return the 8 most recent transactions
        latest_transactions = sorted(added, key=lambda t: t["date"])[-8:]
        return jsonify({"latest_transactions": latest_transactions})

    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)


# Retrieve real-time balance data for each of an Item's accounts
# https://plaid.com/docs/#balance


@bp.route("/api/balance", methods=["GET"])
def get_balance():
    try:
        plaid_client = get_plaid_client()
        request = AccountsBalanceGetRequest(access_token=access_token)
        response = plaid_client.accounts_balance_get(request)
        return jsonify(response.to_dict())
    except plaid.ApiException as e:
        return jsonify(e)


# Retrieve an Item's accounts
# https://plaid.com/docs/#accounts


@bp.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        pretty_print_response(response.to_dict())
        return jsonify(response.to_dict())
    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)


# Retrieve Investment Transactions for an Item
# https://plaid.com/docs/#investments


@bp.route("/api/investments_transactions", methods=["GET"])
def get_investments_transactions():
    # Pull transactions for the last 30 days
    plaid_client = get_plaid_client()
    start_date = datetime.datetime.now() - timedelta(days=(30))
    end_date = datetime.datetime.now()
    try:
        options = InvestmentsTransactionsGetRequestOptions()
        request = InvestmentsTransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date(),
            options=options,
        )
        response = plaid_client.investments_transactions_get(request)
        return jsonify({"error": None, "investments_transactions": response.to_dict()})

    except plaid.ApiException as e:
        return jsonify(e)


@bp.route("/sandbox/create_link_token", methods=["POST"])
def create_sandbox_link_token():
    # Using the form on the management page, search for the selected institution
    # with the Institution Search and Response objects from the Plaid API.
    plaid_client = get_plaid_client()

    inst_request = InstitutionsSearchRequest(
        client_id=session["PLAID_CLIENT_ID"],
        secret=session["PLAID_SECRET"],
        query=request.form["institution"],
        products=[Products("investments")],
        country_codes=[CountryCode("US")],
    )
    inst_response = plaid_client.institutions_search(inst_request)
    # Return the institution id from the institution that matches the
    # institution selected in the html form.
    selected_inst = [
        inst["institution_id"]
        for inst in inst_response["institutions"]
        if inst["name"] == request.form["institution"]
    ][0]
    pt_request = SandboxPublicTokenCreateRequest(
        client_id=session["PLAID_CLIENT_ID"],
        secret=session["PLAID_SECRET"],
        institution_id=selected_inst,
        initial_products=[Products("investments")],
    )
    pt_response = plaid_client.sandbox_public_token_create(pt_request)
    # The generated public_token can now be
    # exchanged for an access_token
    exchange_request = ItemPublicTokenExchangeRequest(
        public_token=pt_response["public_token"]
    )
    exchange_response = plaid_client.item_public_token_exchange(exchange_request)
    session["access_token"] = exchange_response["access_token"]
    session["item_id"] = exchange_response["item_id"]
    return render_template(
        "profile/manager.html",
        tables=[
            pd.read_json(return_portfolio()).to_html(classes="data", header="true")
        ],
        institutions=request_institutions(),
    )


def return_portfolio():
    from collections import defaultdict

    plaid_client = get_plaid_client()
    # Pull Holdings for an Item
    inv_request = InvestmentsHoldingsGetRequest(access_token=session["access_token"])
    response = plaid_client.investments_holdings_get(inv_request)
    # Handle Holdings response
    holdings = response["holdings"]
    # Handle Securities response
    securities = response["securities"]

    portfolio = defaultdict(dict)
    for sec in securities:
        if sec["type"] != "derivative":
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
            portfolio[sec_ticker]["type"] = sec["type"]
            if sec_quant is not None and len(sec_quant) > 0:
                portfolio[sec_ticker]["quantity"] = sec_quant[0]
            if sec_value is not None and len(sec_value) > 0:
                portfolio[sec_ticker]["value"] = sec_value[0]
    return json.dumps(portfolio)


def request_institutions():
    # If a user is logged in, we want to provide them with options
    # to log into a certain portfolio to test.
    plaid_client = get_plaid_client()
    inst_request = InstitutionsGetRequest(
        country_codes=[CountryCode("US")],
        count=500,
        offset=0,
        options=InstitutionsGetRequestOptions(products=[Products("investments")]),
    )

    response = plaid_client.institutions_get(inst_request)
    # With the institutions' response, we can capture the names
    # to display on the front end for our application.
    institutions = [inst["name"] for inst in response["institutions"]]
    institutions.sort()
    return institutions
