# Data visualization libraries
from typing import Union

import plotly.graph_objects as go
import plotly.express as px

# Data manipulation libraries
import pandas as pd
import datetime as dt
import stock_pandas as spd

from functools import cache
from yahoo_fin import stock_info as si
from src.data.yahoo import retrieve_company_stock_price_from_mongo


@cache
def get_tickers():
    # gather stock symbols from major US exchanges
    sp500 = pd.DataFrame(si.tickers_sp500())
    nasdaq = pd.DataFrame(si.tickers_nasdaq())
    dow = pd.DataFrame(si.tickers_dow())

    # convert DataFrame to list, then to sets
    sym1 = set(symbol.replace("$", "-") for symbol in sp500[0].values.tolist())
    sym2 = set(symbol.replace("$", "-") for symbol in nasdaq[0].values.tolist())
    sym3 = set(symbol.replace("$", "-") for symbol in dow[0].values.tolist())

    # join the 4 sets into one. Because it's a set, there will be no duplicate symbols
    symbols = set.union(sym1, sym2, sym3)

    # Some stocks are 5 characters. Those stocks with the suffixes listed below are not of interest.
    my_list = ["W", "R", "P", "Q"]
    del_set = set()

    for symbol in symbols:
        if len(symbol) > 4 and symbol[-1] in my_list:
            del_set.add(symbol)

    tickers = list(symbols.difference(del_set))
    tickers.sort()
    return [symbol[:-2] if "." in symbol else symbol for symbol in tickers]


def transform_dates(start_date: str, end_date: str):
    start_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
    start_date = pd.to_datetime(start_date, format="%Y-%m-%d %H:%M:%S")
    end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")
    end_date = pd.to_datetime(end_date, format="%Y-%m-%d %H:%M:%S")

    return start_date, end_date


def get_kdj_data(ticker, start_date, end_date):
    """
    Returns the level of

    :param ticker:
    :param start_date:
    :param end_date:
    :return tuple: k is the rate a which the
    """
    # Transform dates received as strings from dataframe
    start_date, end_date = transform_dates(start_date, end_date)

    # Retrieve the data from MongoDB and modify column names
    cols = ["Date", "Close", "High", "Low", "Volume"]
    stock_data = retrieve_company_stock_price_from_mongo(ticker)
    stock_df = pd.DataFrame(stock_data)[cols]
    stock_df.columns = [name.lower() for name in cols]

    # Filer the dataframe to the start and end dates specified above
    stock_df = stock_df[(stock_df.date >= start_date) & (stock_df.date <= end_date)]
    stock_df.sort_values(by="date", inplace=True)

    # Leverage stock pandas to get each variable of KDJ and rename resulting columns
    kdj_cols = ["kdj.k", "kdj.d", "kdj.j"]
    stock = spd.StockDataFrame(stock_df)
    kdj = stock[kdj_cols]

    # Update the dataframe to have the human-readable columns and index
    kdj.columns = kdj_cols
    kdj.index = stock_df.date
    kdj = kdj.reset_index()
    return kdj


class kdjChart:
    def __init__(self, ticker: str, data: pd.DataFrame):
        self.chart = None
        self.ticker = ticker
        self.data = data

    def create_chart(self):
        fig = go.Figure()

        signal1, signal2 = self.data["kdj.k"].iat[-1], self.data["kdj.j"].iat[-1]
        kdj = self.data.tail(1)[["kdj.k", "kdj.d", "kdj.j"]].values[0]

        if (
            (signal2 > signal1)
            and (signal1 > self.data["kdj.d"].iat[-1])
            and (kdj > 80).all()
        ):
            signal2 = "might be a good time to buy"
        elif (
            (signal2 < signal1)
            and (signal1 < self.data["kdj.d"].iat[-1])
            and (kdj < 20).all()
        ):
            signal2 = "might be a good time to sell"
        else:
            signal2 = "might be a good time to look at more signals before buying"

        if signal1 >= 80:
            signal1 = "overbought"
        elif signal1 <= 20:
            signal1 = "overbought"
        else:
            signal1 = "being traded normally"

        fig.add_trace(
            go.Scatter(x=self.data.date, y=self.data["kdj.k"], name="K Indicator")
        )

        fig.add_trace(
            go.Scatter(x=self.data.date, y=self.data["kdj.d"], name="D Indicator")
        )

        fig.add_trace(
            go.Scatter(x=self.data.date, y=self.data["kdj.j"], name="J Indicator")
        )

        fig.update_layout(
            {
                "title": {
                    "text": f"KDJ Signals<br><sup>As of {self.data.date.iat[-1].date()}, {self.ticker} is {signal1}, and it {signal2}.</sup>"
                }
            },
            margin=dict(l=50, r=50, b=50, t=70),
            paper_bgcolor="#060606",
            font={"color": "White"},
        )

        self.chart = fig
        return self.chart


class movingAvgChart:
    def __init__(self, ticker: str):
        self.chart = None
        self.ticker = ticker

    def createWMA(
        self,
        window: Union["wma_7", "wma_30", "wma_60", "wma_120"],
        start_date: str,
        end_date: str,
    ):
        """

        :param window: Weighted moving average
        :param start_date:
        :param end_date:
        :return:
        """
        stock_data = retrieve_company_stock_price_from_mongo(self.ticker)
        start_date, end_date = transform_dates(start_date, end_date)
        stock_data = stock_data[
            (stock_data["Date"] >= start_date) & (stock_data["Date"] <= end_date)
        ]
        stock_data.sort_values(by="Date", inplace=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=stock_data.Date, y=stock_data[window], name=window))
        fig.add_trace(go.Scatter(x=stock_data.Date, y=stock_data.Close, name="Close"))
        fig.update_xaxes(tickformat="%b\n%Y")

        fig.update_layout(
            {
                "title": {
                    "text": f"""Weighted Moving Average
                                <br><sup>Check the weighted moving average versus the close to find a sell or buy signal.</sup>"""
                }
            },
            paper_bgcolor="#060606",
            font={"color": "White"},
        )

        self.chart = fig
        return self.chart


if __name__ == "__main__":
    ticker = "TSLA"
    data = get_kdj_data(ticker, "2022-01-10 04:00:00", "2022-10-14 04:00:00")
    kdjChart(ticker=ticker, data=data).create_chart().show()
