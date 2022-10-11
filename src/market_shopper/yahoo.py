import datetime
from datetime import date
import logging
logging.basicConfig(filename='stock_analysis.log', filemode='w', format='%(asctime)s %(message)s', level=logging.DEBUG)
import mongo
from mongo import yahoo_col
# from mongo import ticker_cik
# from mongo import tickers
import numpy as np
import pandas as pd
import pymongo
import yahoo
import yfinance as yf
import ftplib
import sec
from sec import tickers
from sec import ticker_cik
from sec import cik_ticker

yahoo_df_dict = {}

### NOTE - This entire file/section of the code base was completed prior to Milestone II and did not require any changes to work with this project ###


def retrieve_nasdaq_tickers():
    ftp = ftplib.FTP("ftp.nasdaqtrader.com")
    ftp.login()

    handle = open("nasdaqlisted.txt", 'wb')
    filename = '/Symboldirectory/nasdaqlisted.txt'
    ftp.retrbinary('RETR ' + filename, handle.write)
    nasdaq_df = pd.read_csv('nasdaqlisted.txt', sep='|')

    handle = open("otherlisted.txt", 'wb')
    filename = '/Symboldirectory/otherlisted.txt'
    ftp.retrbinary('RETR ' + filename, handle.write)    
    other_df = pd.read_csv('otherlisted.txt', sep='|')

    tickers = list(nasdaq_df['Symbol'])
    tickers = tickers + list(other_df['ACT Symbol'])
    print(len(tickers))
    return tickers

tickers = retrieve_nasdaq_tickers()

def build_yahoo_dict_from_db():
    logging.debug('Entering build_yahoo_dict_from_db')
    stored_tickers = price_yah_col.distinct("ticker")
    for ticker in stored_tickers:
        logging.debug('Adding ' + ticker + ' to yahoo_df_dict')
        yahoo_df_dict[ticker] = retrieve_yahoo_stock_price_df(ticker, "stock_price")
    logging.debug('Exiting build_yahoo_dict_from_db')
    # return yahoo_df_dict

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
    #     print(ser)
    #     print(wma)
    col_name_string = 'wma_' + str(wd_size)
    df[col_name_string] = wma
    # wma = np.array(wma)

    return df

def filter_yahoo_dict(date_range_low, date_range_high):
    """ Filter the DataFrames for the correct Dates, Add a Ticker column """
    for ticker, value in yahoo_df_dict.items():
        yahoo_df_dict[ticker] = value[(value.Date >= date_range_low) & (value.Date <= date_range_high)]
        # av_df_dic[key]['ticker'] = key
        yahoo_df_dict[ticker] = yahoo_df_dict[ticker].reset_index()
        # if (yahoo_df_dict[key].isnull().values.any()==True) or (len(yahoo_df_dict[key])!=253):
        #   print("Missing values found",key)
    # return yahoo_df_dict

def get_yahoo_df_dict():
    return yahoo_df_dict

def initialize_stock_price_yahoo():
    '''
      Initializes stock_price_yahoo collection with tickers from tickers list, querying the Yahoo API for each ticker

              Parameters:
                      None

              Returns:
                      None
    '''
    yahoo_col.drop()
    for ticker in tickers[:5]:
        print("Evaluating ticker: " + ticker)
        yahoo = yf.Ticker(ticker)
        data = yahoo.history(period="max")
        data = calculate_weighted_moving_average(data, 7, 1)
        data = calculate_weighted_moving_average(data, 30, 1)
        data = calculate_weighted_moving_average(data, 60, 1)
        data = calculate_weighted_moving_average(data, 120, 1)
        data.reset_index(inplace=True)
        # csv_name = 'Yahoo/yahoo_' + ticker +'.csv'
        # data.to_csv(csv_name)
        data_dict = data.to_dict("records")
        yahoo_col.insert_one({"cik": int(ticker_cik[ticker]), "ticker": ticker, 'stock_price': data_dict})

def initialize_stock_price_yahoo_multithread(ticker_list):
    '''
      Initializes stock_price_yahoo collection with tickers from tickers list, querying the Yahoo API for each ticker

              Parameters:
                      None

              Returns:
                      None
    '''
    
    for ticker in ticker_list:
        print("Retrieving ticker: " + ticker)
        yahoo = yf.Ticker(ticker)
        data = yahoo.history(period="max")
        data = calculate_weighted_moving_average(data, 7, 1)
        data = calculate_weighted_moving_average(data, 30, 1)
        data = calculate_weighted_moving_average(data, 60, 1)
        data = calculate_weighted_moving_average(data, 120, 1)
        data.reset_index(inplace=True)
        data_dict = data.to_dict("records")
        try:
            yahoo_col.insert_one({"cik": int(mongo.ticker_cik[ticker]), "ticker": ticker, 'stock_price': data_dict})
        except KeyError:
            print("Ticker " + ticker + " not in SEC ticker file")

def retrieve_yahoo_stock_price_df(ticker):
    logging.debug('Entering retrieve_yahoo_stock_price_df')
    logging.debug('Retrieving dataframe for ' + ticker)
    price_query = {"ticker": ticker}
    price_data = yahoo_col.find_one(price_query)
    df = pd.DataFrame(price_data['stock_price'])
    df = convert_date_df(df, 'date')
    # file_name = 'Yahoo/yahoo_' + ticker +'.csv'
    # df = pd.read_csv(file_name)
    # df = convert_date_df(df, 'index')
    return df

def update_stock_price_yahoo():
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
    stored_tickers = price_yah_col.distinct("ticker")

    today = date.today()
    today_date = today.strftime("%Y-%m-%d")

    last_run_date = config_col.find_one({"version": version_num})['initialize_stock_price_yahoo_last_run']
    start_date = last_run_date.strftime("%Y-%m-%d")

    for ticker in stored_tickers:
        logging.debug('Evaluating ticker: ' + ticker)

        # data = yf.download(ticker, start=start_date, end=today_date)

        yahoo = yf.Ticker(ticker)
        data = yahoo.history(start=start_date, end=today_date)
        # stored_df = yahoo_df_dict[ticker]
        stored_df = retrieve_yahoo_stock_price_df(ticker, 'stock_price')
        # date_diff = data.index.difference(stored_df.index)
        drop_dates = list(data.index) - list(stored_df.index)
        logging.debug('drop_dates variable: ' + str(drop_dates))
        data = data.drop(index=drop_dates)
        data.reset_index(inplace=True)
        data_dict = data.to_dict("records")
        price_yah_col.insert_one({"cik": int(ticker_cik[ticker]), "ticker": ticker, 'stock_price': data_dict})
        # price_yah_col.update_many({ "cik": int(ticker_cik[ticker], "ticker": ticker}, {"$push": {array: {'stock_price': data_dict}}}, upsert=True)