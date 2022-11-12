from datetime import date
import datetime
from datetime import datetime as dt

# import logging
# logging.basicConfig(filename='yahoo.log', filemode='w', format='%(asctime)s %(message)s', level=logging.DEBUG)
import src.data.mongo as mongo

# import mongo as mongo
import numpy as np
import pandas as pd
import yfinance as yf
import src.data.sec as sec

# import sec as sec
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
    # start_time = time.perf_counter()
    print("Starting ticker retrieval...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for ticker in tickers:
            executor.submit(retrieve_company_stock_price_from_yahoo, ticker)
    # end_time = time.perf_counter()
    # total_time = end_time - start_time
    # print("Yahoo initiation took " + str(total_time) + " seconds")


def retrieve_company_stock_price_from_yahoo(ticker):
    # print("Retrieving full stock price data for ticker: " + ticker)
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
    # df['cik'] = int(ticker_cik[ticker])
    df["ticker"] = ticker
    df["sector"] = sector
    df["industry"] = industry
    df.at[yesterday_date, "targetLowPrice"] = targetLowPrice
    df.at[yesterday_date, "targetMeanPrice"] = targetMeanPrice
    df.at[yesterday_date, "targetMedianPrice"] = targetMedianPrice
    df.at[yesterday_date, "targetHighPrice"] = targetHighPrice
    df.at[yesterday_date, "numberOfAnalystOpinions"] = numberOfAnalystOpinions
    df.at[yesterday_date, "bookValue"] = bookValue
    # print(df)
    df.reset_index(inplace=True)
    # df_dict = df.to_dict("records")
    yahoo_col.insert_many(df.to_dict("records"))
    # print(df_dict)
    # yahoo_col.insert_one(
    #     {"targetMeanPrice": targetMeanPrice, "targetMedianPrice": targetMedianPrice, "targetHighPrice": targetHighPrice, "numberOfAnalystOpinions": numberOfAnalystOpinions, "stock_price": data_dict}
    # )
    print("Success: " + ticker)


def retrieve_company_stock_price_from_mongo(ticker):
    df = pd.DataFrame()
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    price_data = yahoo_col.find({"ticker": ticker})
    if price_data is not None:
        df = pd.DataFrame(list(price_data))
    return df


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
            # print("Retrieving updated stock price data for ticker: " + ticker)
            start_date_query = max_date + datetime.timedelta(days=1)
            start_date = start_date_query.strftime("%Y-%m-%d")
            today_date = today.strftime("%Y-%m-%d")
            tomorrow_date = tomorrow.strftime("%Y-%m-%d")
            # print(start_date + " " + today_date)
            data = yahoo.history(start=start_date, end=tomorrow_date)
            data_df = pd.DataFrame(data).reset_index()
            # print(data_df)
            df = pd.concat([df, data_df], ignore_index=True)
            # print(df)
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
            # print(df)
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
    # sectors = yahoo_col.distinct("sector")
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
            # pipeline = [
            #     { "$match": {"sector": sector, "stock_price.Date": today_date}},
            #     { "$addFields": {
            #         "order": {
            #             "$filter": {
            #             "input": "$stock_price",
            #             "as": "s",
            #             "cond": { "$eq": [ "$$s.Date", today_date ] }
            #             }
            #         }
            #     }},
            #     { "$sort": { "order.close_pct_1yr": order } }
            #     ]
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
                # print(ticker)
                # print(df)
                count = count + 1
                if count >= 5:
                    break
    yahoo_sectors_col = mydb["yahoo_sectors"]
    results_dict = results_df.to_dict("records")
    yahoo_sectors_col.insert_one(results_dict)
    # print(results_df)
