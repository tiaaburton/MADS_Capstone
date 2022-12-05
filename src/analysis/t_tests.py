import datetime as dt
import os
from collections import defaultdict
from functools import cache
from pathlib import Path
from typing import Union

import pandas as pd
import scipy.stats as stats
import yfinance as yf
from yfinance.utils import get_json

from src.data.yahoo import retrieve_company_stock_price_from_mongo


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
    # data = retrieve_company_stock_price_from_mongo(ticker)
    # if data is None or data.empty:
    data = yf.Ticker(ticker).history("max").reset_index()
    data.Date = data.Date.dt.date
    # start_date = start_date.date()
    # end_date = end_date.date()
    data = data[(data["Date"] >= start_date) & (data["Date"] <= end_date)]
    return data.Close


@cache
def get_available_portfolios():
    directory = Path(__file__).parents[1]
    files = os.listdir(directory)
    portfolios = [f"{directory}/{file}" for file in files if file[-4:] == ".csv"]
    return portfolios


def stock_ttest(
    stock1: str,
    stock2: str,
    idx: Union[None, str] = "SPY",
    start_date: Union[dt.date, dt.datetime] = dt.datetime.today().date(),
    end_date: Union[dt.date, dt.datetime] = dt.datetime.today().date(),
):
    """
    Compares the returns of two stocks with a 2 sided t-test to understand if one stock
    is superior to another and if the result is significant or not.

    :param stock1: Ticker string or dataframe with date and closing price ('Date', 'Close') for a single stock
    :param stock2: Ticker string or dataframe with date and closing price ('Date', 'Close') for a single stock
    :param idx: Ticker representing the stock index to compare to
    :param start_date: Date in which the time series of stock data should start. Ex: dt.datetime(2022,10,31).date()
    :param end_date: Date in which the time series of stock data should end. Ex: dt.datetime.today().date()
    :return: t_statistic, p_val
    """
    if not stock1 or not stock2 or not idx:
        raise ValueError

    # t_stat, p_val = stats.ttest_ind(portfolio, other_data, equal_var=False)
    # return t_stat, p_val

    t_stat = None
    p_val = None
    return t_stat, p_val


def portfolio_ttest(
    portfolio: str = "test_portfolio.csv",
    comp_portfolio: str = "comparison_portfolio.csv",
    start_date: Union[dt.date, dt.datetime] = (
        dt.datetime.today() - dt.timedelta(7)
    ).date(),
    end_date: Union[dt.date, dt.datetime] = dt.datetime.today().date(),
):
    """

    :param portfolio: Ticker string or dataframe with date and closing price ('Date', 'Close') for a primary portfolio
    :param comp_portfolio: Ticker string or dataframe with date and closing price ('Date', 'Close') for a different portfolio
    :param start_date: Date in which the time series of stock data should start. Ex: dt.datetime(2022,10,31).date()
    :param end_date: Date in which the time series of stock data should end. Ex: dt.datetime.today().date()
    :return: t_stat, p_val
    """

    port_tickers = pd.read_csv(
        os.path.join(str(Path(__file__).parents[1]), portfolio)
    ).Symbol
    comp_tickers = pd.read_csv(
        os.path.join(str(Path(__file__).parents[1]), comp_portfolio)
    ).Symbol
    dates = pd.date_range(start_date, end_date)

    port = pd.DataFrame(columns=port_tickers)
    comp = pd.DataFrame(columns=comp_tickers)

    for ticker in port_tickers:
        port[ticker] = transform_data(ticker, start_date, end_date).values

    for ticker in comp_tickers:
        comp[ticker] = transform_data(ticker, start_date, end_date).values

    port.index = dates[: len(port)]
    comp.index = dates[: len(comp)]
    return port, comp

    # t_stat, p_val = stats.ttest_ind(portfolio, comp_portfolio, equal_var=False)
    # return t_stat, p_val


class stockTTestChart:
    def __init__(self):
        self.chart = None
        self.data = None


if __name__ == "__main__":
    print(get_holdings("SPY"))
