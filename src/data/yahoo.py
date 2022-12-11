from datetime import date
import datetime
from datetime import datetime as dt

import src.data.sec as sec
import src.data.mongo as mongo

# Below libraries are used to run the code outside of the Docker image
# from data import mongo
# from data import sec

import numpy as np
import pandas as pd
import yfinance as yf
import pymongo
import concurrent.futures
import time

ticker_cik = {}
index_tickers = [
    "^GSPC",
    "SPX",
    "SPY",
    "^VIX",
    "^VVIX",
    "^SKEW",
    "CL=F",
    "HG=F",
    "GC=F",
    "^DJI",
]

### Below method reused from Joshua Raymond's Milestone II Project ###
def calculate_weighted_moving_average(df, wd_size, weights=1):
    """
    Takes in a Yahoo Stock Price dataframe and calculates the WMA with a window size of wd_size

            Parameters:
                    df (dataframe): stock_price_yahoo dataframe
                    wd_size (int): Window size for weighted moving average
                    weights (int): Weights for each item, default of 1

            Returns:
                    df (dataframe): Updated dataframe with wma_[wd_size] column added
    """
    ser = df["Close"]
    wma = []
    if isinstance(weights, int):
        weights = np.full(wd_size, weights, dtype=float)

    assert (
        len(weights) == wd_size
    ), "The size of the weights must be the same as the window size. "

    last_items = []
    for item in ser:
        last_items.append(item)
        length = len(last_items)
        if length < 2:
            average = last_items[-1:][0]
        elif length < wd_size:
            average = (
                np.dot(last_items[-length:], weights[-length:])
                / weights[-length:].sum()
            )
        else:
            average = np.dot(last_items[-wd_size:], weights) / weights.sum()
        wma.append(average)
    col_name_string = "wma_" + str(wd_size)
    df[col_name_string] = wma

    return df


def initialize_yahoo():
    global ticker_cik
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    yahoo_col.drop()
    companies_df = sec.retrieve_companies_from_sec()
    tickers = list(companies_df["ticker"]) + index_tickers
    ticker_cik = sec.retrieve_ticker_cik_from_mongo()
    print("Starting ticker retrieval...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for ticker in tickers:
            executor.submit(retrieve_company_stock_price_from_yahoo, ticker)
    create_indices_in_mongo()


def create_indices_in_mongo():
    mydb = mongo.get_mongo_connection()
    print("Creating indices...")
    yahoo_col = mydb["yahoo"]
    yahoo_col.create_index("ticker")
    yahoo_col.create_index("Date")
    yahoo_col.create_index("sector")
    yahoo_col.create_index("industry")
    yahoo_col.create_index(
        [("Date", pymongo.DESCENDING), ("sector", pymongo.ASCENDING)],
        name="date_sector",
    )
    yahoo_col.create_index(
        [("Date", pymongo.DESCENDING), ("ticker", pymongo.ASCENDING)],
        name="date_ticker",
    )

### Below method partly reused (expanded for this project) from Joshua Raymond's Milestone II Project ###
def retrieve_company_stock_price_from_yahoo(ticker):
    today = date.today()
    today_date = today.strftime("%Y-%m-%d")
    yesterday = date.today() + datetime.timedelta(days=-1)
    yesterday_date = yesterday.strftime("%Y-%m-%d")
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    yahoo = yf.Ticker(ticker)
    sector = yahoo.info["sector"]
    industry = yahoo.info["industry"]
    targetLowPrice = yahoo.info["targetLowPrice"]
    targetMeanPrice = yahoo.info["targetMeanPrice"]
    targetMedianPrice = yahoo.info["targetMedianPrice"]
    targetHighPrice = yahoo.info["targetHighPrice"]
    numberOfAnalystOpinions = yahoo.info["numberOfAnalystOpinions"]
    bookValue = yahoo.info["bookValue"]
    df = yahoo.history(period="10y")
    df = calculate_weighted_moving_average(df, 7, 1)
    df = calculate_weighted_moving_average(df, 30, 1)
    df = calculate_weighted_moving_average(df, 60, 1)
    df = calculate_weighted_moving_average(df, 120, 1)
    df["close_pct_1d"] = df["Close"].pct_change()
    df["close_pct_30d"] = df["Close"].pct_change(periods=20)
    df["close_pct_60d"] = df["Close"].pct_change(periods=40)
    df["close_pct_120d"] = df["Close"].pct_change(periods=80)
    df["close_pct_1yr"] = df["Close"].pct_change(periods=260)
    df["log_return_1d"] = np.log(df["Close"]/df["Close"].shift(1))
    df["log_return_30d"] = np.log(df["Close"]/df["Close"].shift(20))
    df["log_return_60d"] = np.log(df["Close"]/df["Close"].shift(40))
    df["log_return_120d"] = np.log(df["Close"]/df["Close"].shift(80))
    df["log_return_1yr"] = np.log(df["Close"]/df["Close"].shift(260))
    df["ticker"] = ticker
    df["sector"] = sector
    df["industry"] = industry
    df.at[yesterday_date, "targetLowPrice"] = targetLowPrice
    df.at[yesterday_date, "targetMeanPrice"] = targetMeanPrice
    df.at[yesterday_date, "targetMedianPrice"] = targetMedianPrice
    df.at[yesterday_date, "targetHighPrice"] = targetHighPrice
    df.at[yesterday_date, "numberOfAnalystOpinions"] = numberOfAnalystOpinions
    df.at[yesterday_date, "bookValue"] = bookValue
    df["targetMedianGrowth"] = (df["targetMedianPrice"] - df["Close"]) / df[
        "targetMedianPrice"
    ]
    df.reset_index(inplace=True)
    df_dict = df.to_dict("records")
    yahoo_col.insert_many(df.to_dict("records"))
    print("Success: " + ticker)


def retrieve_company_stock_price_from_mongo(ticker):
    df = pd.DataFrame()
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    price_data = yahoo_col.find({"ticker": ticker})
    if price_data is not None:
        df = pd.DataFrame(list(price_data))
    return df

### Below method partly reused (expanded for this project) from Joshua Raymond's Milestone II Project ###
def update_company_stock_price_from_yahoo(ticker):
    print("Updating stock price data for ticker: " + ticker)
    global ticker_cik
    ticker_cik = sec.retrieve_ticker_cik_from_mongo()
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    price_data = yahoo_col.find_one({"ticker": ticker})
    if price_data is not None:
        yahoo = yf.Ticker(ticker)
        targetLowPrice = yahoo.info["targetLowPrice"]
        targetMeanPrice = yahoo.info["targetMeanPrice"]
        targetMedianPrice = yahoo.info["targetMedianPrice"]
        targetHighPrice = yahoo.info["targetHighPrice"]
        numberOfAnalystOpinions = yahoo.info["numberOfAnalystOpinions"]
        df = pd.DataFrame(price_data["stock_price"])
        df["Date"] = pd.to_datetime(df["Date"].dt.strftime("%Y-%m-%d"))
        max_date = df["Date"].max().to_pydatetime()
        today = date.today()
        tomorrow = date.today() + datetime.timedelta(days=1)
        if max_date.date() < today:
            start_date_query = max_date + datetime.timedelta(days=1)
            start_date = start_date_query.strftime("%Y-%m-%d")
            today_date = today.strftime("%Y-%m-%d")
            tomorrow_date = tomorrow.strftime("%Y-%m-%d")
            data = yahoo.history(start=start_date, end=tomorrow_date)
            data_df = pd.DataFrame(data).reset_index()
            df = pd.concat([df, data_df], ignore_index=True)
            df.set_index("Date", inplace=True)
            df = calculate_weighted_moving_average(df, 7, 1)
            df = calculate_weighted_moving_average(df, 30, 1)
            df = calculate_weighted_moving_average(df, 60, 1)
            df = calculate_weighted_moving_average(df, 120, 1)
            df["close_pct_1d"] = df["Close"].pct_change()
            df["close_pct_30d"] = df["Close"].pct_change(periods=20)
            df["close_pct_60d"] = df["Close"].pct_change(periods=40)
            df["close_pct_120d"] = df["Close"].pct_change(periods=80)
            df["close_pct_1yr"] = df["Close"].pct_change(periods=260)
            df.at[today_date, "targetLowPrice"] = targetLowPrice
            df.reset_index(inplace=True)
            data_dict = df.to_dict("records")
            yahoo_col.update_one(
                {"ticker": ticker}, {"$set": {"stock_price": data_dict}}
            )
    else:
        retrieve_company_stock_price_from_yahoo(ticker)


def update_yahoo_daily():
    companies_df = sec.retrieve_companies_from_mongo()
    tickers = list(companies_df["ticker"]) + index_tickers
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for ticker in tickers:
            executor.submit(update_company_stock_price_from_yahoo, ticker)


def calculate_stock_performance_by_sector():
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    sectors = [
        "Basic Materials",
        "Communication Services",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Energy",
        "Financial",
        "Financial Services",
        "Healthcare",
        "Industrials",
        "Real Estate",
        "Technology",
        "Utilities",
    ]
    today_date = dt.combine(date.today(), dt.min.time())
    orders = [-1, 1]
    results_df = pd.DataFrame()
    for sector in sectors:
        for order in orders:
            pipeline = [
                {"$match": {"sector": sector, "stock_price.Date": today_date}},
                {
                    "$addFields": {
                        "order": {
                            "$filter": {
                                "input": "$stock_price",
                                "as": "s",
                                "cond": {
                                    "$and": [
                                        {"$eq": ["$$s.Date", today_date]},
                                        {"$ne": ["$$s.close_pct_1yr", None]},
                                    ]
                                },
                            }
                        }
                    }
                },
                {"$sort": {"order.close_pct_1yr": order}},
            ]
            top_growth = yahoo_col.aggregate(pipeline, allowDiskUse=True)
            count = 0
            for growth in top_growth:
                ticker = growth["ticker"]
                df = pd.DataFrame(growth["stock_price"])
                df["ticker"] = ticker
                df["sector"] = sector
                df = df[df["Date"] == today_date]
                results_df = pd.concat([results_df, df], ignore_index=True)
                count = count + 1
                if count >= 5:
                    break
    yahoo_sectors_col = mydb["yahoo_sectors"]
    results_dict = results_df.to_dict("records")
    yahoo_sectors_col.insert_one(results_dict)


def retrieve_stocks_by_sector(top_n):
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    sectors = [
        "Basic Materials",
        "Communication Services",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Energy",
        "Financial",
        "Financial Services",
        "Healthcare",
        "Industrials",
        "Real Estate",
        "Technology",
        "Utilities",
    ]
    results_df = pd.DataFrame()
    for sector in sectors[1:2]:
        last_date = list(yahoo_col.find().sort("Date", -1).limit(1))[0]["Date"]
        sector_df = pd.DataFrame(
            list(yahoo_col.find({"Date": last_date, "sector": sector}))
        )
        sector_df.dropna(subset=["close_pct_1yr"], inplace=True)
        sector_df.sort_values(by=["close_pct_1yr"], ascending=False, inplace=True)
        print(sector_df["close_pct_1yr"])
    # print(results_df)


def retrieve_stocks_by_growth():
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    results_df = pd.DataFrame()
    last_date = list(yahoo_col.find().sort("Date", -1).limit(1))[0]["Date"]
    results_df = pd.DataFrame(list(yahoo_col.find({"Date": last_date})))
    results_df.dropna(subset=["close_pct_1yr"], inplace=True)
    results_df.sort_values(by=["close_pct_1yr"], ascending=False, inplace=True)
    return results_df


def retrieve_stocks_by_analyst():
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    results_df = pd.DataFrame()
    last_date = list(yahoo_col.find().sort("Date", -1).limit(1))[0]["Date"]
    results_df = pd.DataFrame(list(yahoo_col.find({"Date": last_date})))
    results_df.dropna(
        subset=["numberOfAnalystOpinions", "targetMedianPrice"], inplace=True
    )
    results_df.sort_values(
        by=["numberOfAnalystOpinions"], ascending=False, inplace=True
    )
    return results_df
