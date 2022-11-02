import numpy as np
import scipy.stats as stats
import pandas as pd
import datetime as dt
import pyspark
import pprint
import json
from collections import defaultdict
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import yfinance as yf
from src.data.yahoo import retrieve_company_stock_price_from_mongo
from yfinance.utils import get_json

spark = SparkSession.builder.appName("Market-Shopper").master("local[*]").getOrCreate()
spark.sparkContext.setLogLevel("DEBUG")


def get_holdings(ticker: str):
    holdings = defaultdict(list)
    data = yf.utils.get_json(f"https://finance.yahoo.com/quote/{ticker}")[
        "topHoldings"
    ]["holdings"]
    for stock in data:
        holdings[ticker].append(stock["symbol"])
    return holdings


def transform_data(
    ticker,
    start_date: Union[dt.date, dt.datetime],
    end_date: Union[dt.date, dt.datetime],
):
    """
    Function to retrieve and limit data if needed.
    :param ticker:
    :param start_date:
    :param end_date:
    :return:
    """
    data = retrieve_company_stock_price_from_mongo(ticker)
    if data.empty:
        data = yf.Ticker(ticker).history("max")
    data = data[(data["Date"] >= start_date) & (data["Date"] <= end_date)]
    return data


def stock_ttest(
    stock1: Union[str, pd.DataFrame, pyspark.sql.DataFrame],
    /,
    stock2: Union[None, str, dict, pd.DataFrame, pyspark.sql.DataFrame] = None,
    idx: Union[None, str] = "SPY",
    start_date: Union[dt.date, dt.datetime] = dt.datetime.today().date(),
    end_date: Union[dt.date, dt.datetime] = dt.datetime.today().date(),
):
    """
    Compares the returns of two stocks with a 2 sided t-test to understand if one stock
    is superior to another and if the result is significant or not.
    :param idx:
    :param stock1: Ticker string or dataframe with date and closing price ('Date', 'Close') for a single stock
    :param stock2: Ticker string or dataframe with date and closing price ('Date', 'Close') for a single stock
    :param start_date: Date in which the time series of stock data should start. Ex: dt.datetime(2022,10,31).date()
    :param end_date: Date in which the time series of stock data should end. Ex: dt.datetime.today().date()
    :return: t_statistic, p_val
    """
    if not stock1 and not stock2 and not idx:
        raise ValueError

    if stock2 and not idx:
        ...

    if idx and not stock2:
        df = pd.DataFrame()
        holdings = get_holdings(idx)
        for holding in holdings[idx]:
            transform_data(holding)

    t_stat = None
    # mongo_data = mongo_data[(mongo_data["Date"] >= start_date) & (mongo_data["Date"] <= end_date)]
    p_val = None
    return t_stat, p_val


def portfolio_ttest(
    portfolio: Union[pd.DataFrame, pyspark.sql.DataFrame],
    other: Union[str, pd.DataFrame, pyspark.sql.DataFrame] = "SPY",
    start_date: Union[dt.date, dt.datetime] = dt.datetime.today().date(),
    end_date: Union[dt.date, dt.datetime] = dt.datetime.today().date(),
):
    """

    :param portfolio: Ticker string or dataframe with date and closing price ('Date', 'Close') for a primary portfolio
    :param other: Ticker string or dataframe with date and closing price ('Date', 'Close') for a different portfolio
    :param start_date: Date in which the time series of stock data should start. Ex: dt.datetime(2022,10,31).date()
    :param end_date: Date in which the time series of stock data should end. Ex: dt.datetime.today().date()
    :return: t_stat, p_val
    """
    if type(other) == str:
        other_data = retrieve_company_stock_price_from_mongo(other)
        if other_data is None or other_data.empty:
            other_data = yf.Ticker(other).history("max")
    # return other_data
    t_stat, p_val = stats.ttest_ind(portfolio, other_data, equal_var=False)
    return t_stat, p_val


if __name__ == "__main__":
    print(get_holdings("SPY"))
