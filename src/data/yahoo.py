from datetime import date
import datetime
# import logging
# logging.basicConfig(filename='yahoo.log', filemode='w', format='%(asctime)s %(message)s', level=logging.DEBUG)
import src.data.mongo as mongo
import numpy as np
import pandas as pd
import yfinance as yf
import src.data.sec as sec
import concurrent.futures
import time

ticker_cik = {}


def calculate_weighted_moving_average(df, wd_size, weights=1):
    '''
    Takes in a Yahoo Stock Price dataframe and calculates the WMA with a window size of wd_size

            Parameters:
                    df (dataframe): stock_price_yahoo dataframe
                    wd_size (int): Window size for weighted moving average
                    weights (int): Weights for each item, default of 1

            Returns:
                    df (dataframe): Updated dataframe with wma_[wd_size] column added
    '''
    ser = df['Close']
    wma = []
    if isinstance(weights, int):
        weights = np.full(wd_size, weights, dtype=float)

    assert len(weights) == wd_size, "Q4: The size of the weights must be the same as the window size. "

    last_items = []
    for item in ser:
        last_items.append(item)
        length = len(last_items)
        if (length < 2):
            average = last_items[-1:][0]
        elif (length < wd_size):
            average = np.dot(last_items[-length:], weights[-length:]) / weights[-length:].sum()
        else:
            average = np.dot(last_items[-wd_size:], weights) / weights.sum()
        wma.append(average)
    col_name_string = 'wma_' + str(wd_size)
    df[col_name_string] = wma

    return df


def initialize_yahoo():
    global ticker_cik
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    yahoo_col.drop()
    companies_df = sec.retrieve_companies_from_sec()
    tickers = list(companies_df['ticker'])
    ticker_cik = sec.retrieve_ticker_cik_from_mongo()
    # start_time = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for ticker in tickers:
            executor.submit(retrieve_company_stock_price_from_yahoo, ticker)
    # end_time = time.perf_counter()
    # total_time = end_time - start_time
    # print("Yahoo initiation took " + str(total_time) + " seconds")


def retrieve_company_stock_price_from_yahoo(ticker):
    # print("Retrieving full stock price data for ticker: " + ticker)
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    yahoo = yf.Ticker(ticker)
    data = yahoo.history(period="max")
    data = calculate_weighted_moving_average(data, 7, 1)
    data = calculate_weighted_moving_average(data, 30, 1)
    data = calculate_weighted_moving_average(data, 60, 1)
    data = calculate_weighted_moving_average(data, 120, 1)
    data.reset_index(inplace=True)
    data_dict = data.to_dict("records")
    yahoo_col.insert_one({"cik": int(ticker_cik[ticker]), "ticker": ticker, 'stock_price': data_dict})
    print("Success: " + ticker)
    # return ("Success: " + ticker)


def retrieve_company_stock_price_from_mongo(ticker):
    df = pd.DataFrame()
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    price_data = yahoo_col.find_one({"ticker": ticker})
    if price_data is not None:
        df = pd.DataFrame(price_data['stock_price'])
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
        df = pd.DataFrame(price_data['stock_price'])
        max_date = df['Date'].max().to_pydatetime()
        today = date.today()
        if max_date.date() < today:
            # print("Retrieving updated stock price data for ticker: " + ticker)
            start_date_query = max_date + datetime.timedelta(days=1)
            start_date = start_date_query.strftime("%Y-%m-%d")
            today_date = today.strftime("%Y-%m-%d")
            data = yahoo.history(start=start_date, end=today_date)
            data_df = pd.DataFrame(data).reset_index()
            df = pd.concat([df, data_df])
            df.set_index("Date", inplace=True)
            df = calculate_weighted_moving_average(df, 7, 1)
            df = calculate_weighted_moving_average(df, 30, 1)
            df = calculate_weighted_moving_average(df, 60, 1)
            df = calculate_weighted_moving_average(df, 120, 1)
            df.reset_index(inplace=True)
            data_dict = df.to_dict("records")
            yahoo_col.update_one({"ticker": ticker}, {"$set": {'stock_price': data_dict}})
    else:
        retrieve_company_stock_price_from_yahoo(ticker)


def update_yahoo_daily():
    companies_df = sec.retrieve_companies_from_mongo()
    tickers = list(companies_df['ticker'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for ticker in tickers:
            executor.submit(update_company_stock_price_from_yahoo, ticker)
