from datetime import date
import logging
logging.basicConfig(filename='yahoo.log', filemode='w', format='%(asctime)s %(message)s', level=logging.DEBUG)
import mongo
import numpy as np
import pandas as pd
import yfinance as yf
import sec
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
        for ticker in tickers[:100]:
            executor.submit(retrieve_company_stock_price_from_yahoo, ticker)
    # end_time = time.perf_counter()
    # total_time = end_time - start_time
    # print("Yahoo initiation took " + str(total_time) + " seconds")


def retrieve_company_stock_price_from_yahoo(ticker):
    print("Retrieving Yahoo stock price data for ticker: " + ticker)
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
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    price_query = {"ticker": ticker}
    price_data = yahoo_col.find_one(price_query)
    df = pd.DataFrame(price_data['stock_price'])
    return df

def update_yahoo_daily():
    '''
      Updates stock_price_yahoo collection with new market data, keeping existing market data and appending new dates

              Parameters:
                      None

              Returns:
                      None
    '''
    logging.debug('Entering update_yahoo_stock_price')
    # Initialize yahoo dictionary
    # build_yahoo_dict_from_db()
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    # Change below line to check sec company file
    stored_tickers = yahoo_col.distinct("ticker")

    # Check dates for yahoo col, if company doesn't exist, pull full data, otherwise, pull incremental data



    today = date.today()
    today_date = today.strftime("%Y-%m-%d")

    # last_run_date = config_col.find_one({"version": version_num})['initialize_stock_price_yahoo_last_run']
    # start_date = last_run_date.strftime("%Y-%m-%d")

    for ticker in stored_tickers:
        logging.debug('Evaluating ticker: ' + ticker)

        # data = yf.download(ticker, start=start_date, end=today_date)

        yahoo = yf.Ticker(ticker)
        data = yahoo.history(start=start_date, end=today_date)
        # stored_df = yahoo_df_dict[ticker]
        stored_df = retrieve_company_stock_price_from_mongo(ticker)
        # date_diff = data.index.difference(stored_df.index)
        drop_dates = list(data.index) - list(stored_df.index)
        logging.debug('drop_dates variable: ' + str(drop_dates))
        data = data.drop(index=drop_dates)
        data.reset_index(inplace=True)
        data_dict = data.to_dict("records")
        yahoo_col.insert_one({"cik": int(ticker_cik[ticker]), "ticker": ticker, 'stock_price': data_dict})
        # price_yah_col.update_many({ "cik": int(ticker_cik[ticker], "ticker": ticker}, {"$push": {array: {'stock_price': data_dict}}}, upsert=True)