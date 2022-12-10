from asyncio import format_helpers
import pandas as pd
import urllib.request
import json
import src.data.mongo as mongo
# from data import mongo

import requests
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
from datetime import datetime
import urllib.request
from io import StringIO
import concurrent.futures
import collections

tickers = []
ciks = []
cik_ticker = {}
ticker_cik = {}
headers = {
    "User-Agent": "Masters Project josharay@umich.edu",
    "Accept-Encoding": "gzip, deflate, br",
}


def retrieve_companies_from_sec():
    global tickers
    global ciks
    global ticker_cik
    global cik_ticker
    with urllib.request.urlopen(
        "https://www.sec.gov/files/company_tickers.json"
    ) as url:
        data = json.load(url)
    sec_df = pd.DataFrame.from_dict(data).T
    tickers = list(sec_df["ticker"])
    ciks = list(sec_df["cik_str"])
    ticker_cik = dict(zip(list(sec_df["ticker"]), list(sec_df["cik_str"])))
    cik_ticker = dict(zip(list(sec_df["cik_str"]), list(sec_df["ticker"])))
    # print(sec_df)
    return sec_df


def insert_companies_into_mongo():
    sec_df = retrieve_companies_from_sec()

    mydb = mongo.get_mongo_connection()
    sec_companies_col = mydb["companies"]
    sec_companies_col.drop()
    sec_companies_col.insert_many(sec_df.to_dict("records"))


def retrieve_companies_from_mongo():
    mydb = mongo.get_mongo_connection()
    sec_companies_col = mydb["companies"]
    companies_df = pd.DataFrame(list(sec_companies_col.find({})))
    # print(companies_df.head())
    return companies_df


def retrieve_ticker_cik_from_mongo():
    companies_df = retrieve_companies_from_mongo()
    ticker_cik = dict(zip(list(companies_df["ticker"]), list(companies_df["cik_str"])))
    return ticker_cik


@on_exception(expo, RateLimitException, max_tries=3)
@limits(calls=10, period=1)
def retrieve_company_facts_from_sec(cik):
    print("Retrieving SEC company facts for cik: " + str(cik))
    facts_url = (
        "https://data.sec.gov/api/xbrl/companyfacts/CIK"
        + str.zfill(str(cik), 10)
        + ".json"
    )
    response_json = None
    try:
        response_http = requests.get(facts_url, headers=headers)
        response_json = response_http.json()
        response_json.update({"ticker": cik_ticker[cik]})
        response_json.update({"cik": int(cik)})
    except requests.exceptions.HTTPError as err:
        print("Could not find SEC data for " + str(cik))
    except json.decoder.JSONDecodeError as err:
        print("Error processing JSON for " + str(cik))
    except KeyError:
        print("Could not find ticker for " + str(cik))
    return response_json


def retrieve_company_submissions_from_sec(cik):
    submissions_url = (
        "https://data.sec.gov/submissions/CIK" + str.zfill(str(cik), 10) + ".json"
    )
    response_http = requests.get(submissions_url, headers=headers)
    response_json = response_http.json()

    return response_json


def insert_company_facts_into_mongo(cik):
    fact_json = retrieve_company_facts_from_sec(cik)

    if fact_json is not None:
        remove_company_facts_from_mongo(cik)

        mydb = mongo.get_mongo_connection()
        sec_col = mydb["sec"]
        sec_col.insert_one(fact_json)


def remove_company_facts_from_mongo(cik):
    mydb = mongo.get_mongo_connection()
    sec_col = mydb["sec"]
    sec_col.delete_one({"cik": int(cik)})
    # sec_col.delete_many({"cik": str.zfill(str(cik), 10)})


def retrieve_company_facts_from_mongo_using_cik(cik):
    mydb = mongo.get_mongo_connection()
    sec_col = mydb["sec"]
    facts_json = sec_col.find_one({"cik": cik})
    flattened_df = flatten_facts_json(facts_json)
    return flattened_df


def retrieve_company_facts_from_mongo_using_ticker(ticker: str):
    mydb = mongo.get_mongo_connection()
    sec_col = mydb["sec"]
    facts_json = sec_col.find_one({"ticker": ticker})
    flattened_df = flatten_facts_json(facts_json)
    return flattened_df


def retrieve_companies_with_facts_from_mongo():
    mydb = mongo.get_mongo_connection()
    sec_col = mydb["sec"]
    ciks_list = list(sec_col.find({}, {"cik": 1, "_id": False}))
    ciks = [int(value["cik"]) for value in ciks_list if len(value) > 0]
    return ciks


def flatten_facts_json(unflattened_json):
    combined_df = pd.DataFrame()
    try:
        for item in unflattened_json["facts"]:
            temp_df = pd.DataFrame.from_dict(unflattened_json["facts"][item]).T
            combined_df = pd.concat([combined_df, temp_df])
        all_df = None
        first = True
        for index, row in combined_df.iterrows():
            unit_type = str(list(row["units"].keys())[0])
            df = pd.DataFrame(row["units"][unit_type])
            df["unit_type"] = unit_type
            df["measure"] = index
            if first:
                all_df = df
                first = False
            else:
                all_df = pd.concat([all_df, df])
    except TypeError:
        print("Unable to retrieve SEC data for ticker")
        return None
    except KeyError as e:
        print("Key Error when parsing SEC json")
        return None
    except Exception as e:
        print("Exception with SEC data: " + e)
        return None
    return all_df


def initialize_sec():
    insert_companies_into_mongo()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for cik in list(set(ciks)):
            executor.submit(insert_company_facts_into_mongo, cik)
            # insert_company_facts_into_mongo(cik)
    create_indices_in_mongo()


def initialize_remaining_sec():
    insert_companies_into_mongo()
    inserted_ciks = retrieve_companies_with_facts_from_mongo()
    remaining_ciks = list(set(ciks).difference(set(inserted_ciks)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for cik in remaining_ciks:
            executor.submit(insert_company_facts_into_mongo, cik)


def update_sec_daily():
    insert_companies_into_mongo()
    today_year = datetime.today().strftime("%Y")
    today_quarter = "QTR" + str((int(datetime.today().strftime("%m")) - 1) // 3 + 1)
    today_string = datetime.today().strftime("%Y%m%d")

    daily_index_url = (
        "https://www.sec.gov/Archives/edgar/daily-index/"
        + today_year
        + "/"
        + today_quarter
        + "/"
        + "company."
        + "20221017"
        + ".idx"
    )
    response_http = requests.get(daily_index_url, headers=headers)
    data = StringIO(response_http.text)

    daily_index_df = pd.read_csv(data, delimiter=r"[ ]{2,}", skiprows=11, header=None)
    daily_index_df = daily_index_df.rename(
        columns={
            0: "Company Name",
            1: "Form Type",
            2: "CIK",
            3: "Date Filed",
            4: "File Name",
        }
    )
    daily_index_df_10 = daily_index_df[
        (daily_index_df["Form Type"] == "10-Q")
        | (daily_index_df["Form Type"] == "10-K")
    ]
    # print(daily_index_df_10.head())
    print("New 10-Q/10-K files found for: \n")
    print(set(daily_index_df_10["CIK"]))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for cik in set(daily_index_df_10["CIK"]):
            insert_company_facts_into_mongo(cik)

def create_indices_in_mongo():
    mydb = mongo.get_mongo_connection()
    print("Creating indices...")
    yahoo_col = mydb["sec"]
    yahoo_col.create_index('ticker')
    yahoo_col.create_index('cik')