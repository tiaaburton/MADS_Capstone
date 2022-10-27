from pprint import pprint
from typing import Union

# from src.data import sec
from scipy.stats import norm
from src.data.yahoo import retrieve_company_stock_price_from_mongo
import plaid

import pymongo
import configparser
import json
import os

import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
import pyfolio as pf
import src.data.mongo as mongo

from scipy.stats import norm
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark
from pathlib import Path

spark = SparkSession.builder.getOrCreate()


class VaR_Chart:
    def __init__(self):
        self.data = None
        self.chart = None

    @staticmethod
    def test_portfolio(df_type: str = Union['pandas', 'spark']):
        """
        Sample portfolio used to complete functions. Will replace in analysis page with
        portfolio data.

        :return: Returns a pandas or spark dataframe with a test portfolio.
        """
        test_str = f'{str(Path(__file__).parents[4])}/Downloads/test_portfolio.csv'
        portfolio = spark.read.csv(test_str, header=True)
        portfolio = portfolio.withColumnRenamed('Price', 'Close')
        portfolio = portfolio.withColumnRenamed('Symbol', 'Ticker')
        denominator = portfolio.select('Share').agg({'Share': 'sum'}).collect()[0][0]
        portfolio = portfolio.withColumn('Weight', round(col('Share') / lit(denominator), 3))

        if df_type == 'pandas':
            portfolio = portfolio.toPandas()

        return portfolio.head()

    @staticmethod
    def get_portfolio_weights(portfolio: dict[str, dict]):
        """
        Calculates the total of a portfolio (dict(str:dict))
        then computes the weight for each stock within the
        portfolio. Stock weights will be used in VaR.

        Return:
            portfolio: dict
        """
        portfolio_stocks = list(portfolio.keys())
        portfolio_value = 0
        for stock in portfolio_stocks:
            if "value" in portfolio[stock]:
                portfolio_value += portfolio[stock]["value"]

        for stock in portfolio_stocks:
            if "value" in portfolio[stock]:
                stock_weight = portfolio[stock]["value"] / portfolio_value
                portfolio[stock]["weight"] = round(stock_weight, 3)

        assert (
                np.isclose(
                    [
                        round(
                            sum(
                                [
                                    portfolio[stock]["weight"]
                                    for stock in portfolio_stocks
                                    if "weight" in portfolio[stock]
                                ]
                            ),
                            2,
                        )
                    ],
                    [1.0],
                )
                == True
        ).all()

        return portfolio

    @staticmethod
    def _transformer(
            data: Union[None, dict[str, dict], pd.DataFrame, pyspark.sql.DataFrame]
            , start: dt.datetime = dt.date.today()
            , end: dt.datetime = dt.date.today()
    ):
        data["Date"] = pd.to_datetime(data["Date"]).dt.date
        data = data[(data["Date"] >= start) & (data["Date"] <= end)]
        data["Close"] = data["Close"].pct_change()
        return data

    def calculate_VaR(
            self,
            portfolio: Union[None, dict[str, dict], pd.DataFrame, pyspark.sql.DataFrame],
            initial_investment: Union[float, int] = 0,
            start: dt.datetime = dt.date.today(),
            end: dt.datetime = dt.date.today(),
            conf_level: Union[float, int] = 0.05
    ):
        """
        Calculates the Value at Risk overtime.
        Retrieved from https://www.interviewqs.com/blog/value-at-risk

        Return:
            Value at Risk: value or dataframe
        """

        if portfolio is None:
            return 0.0

        if initial_investment == 0 and portfolio is not None:
            if type(portfolio) == dict:
                ...
            elif type(portfolio) == pyspark.sql.DataFrame:
                portfolio = portfolio.toPandas()

            costs = portfolio['Cost'].apply(lambda cost: cost.replace('$', '')).astype(float).values
            shares = portfolio['Share'].astype(float).values
            initial_investment = np.dot(costs, shares)
            print(initial_investment)
            weights = portfolio['Weight']
            portfolio.select('Ticker').toPandas().values
            returns = self._transformer()

        cov_matrix = returns.cov()
        avg_rets = returns.mean()  # Calculate mean returns for each stock

        # Calculate mean returns for portfolio overall, using mean, using dot product formula to
        # normalize against investment weights
        port_mean = avg_rets.dot(weights)

        # Calculate portfolio standard deviation
        port_stdev = np.sqrt(weights.T.dot(cov_matrix).dot(weights))

        # Calculate mean of given investment
        mean_investment = (1 + port_mean) * initial_investment

        # Calculate standard deviation of given investment
        stdev_investment = initial_investment * port_stdev

        # Using SciPy ppf method to generate values for the inverse cumulative distribution function to a normal
        # distribution. Plugging in the mean, standard deviation of our portfolio as calculated above
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
        cutoff1 = norm.ppf(conf_level, mean_investment, stdev_investment)

        # Finally, we can calculate the VaR at our confidence interval
        var_1d1 = initial_investment - cutoff1

        # Create the number of days to determine if a full dataframe needs to be created
        num_days = (start - end).days
        if num_days == 0:
            return var_1d1

        # Calculate n Day VaR with 95% confidence level
        else:
            var_array = [(0, var_1d1)]
            for x in range(1, num_days + 1):
                varOnDay = np.round(var_1d1 * np.sqrt(x), 2)
                var_array.append((x, varOnDay))

            if type(portfolio) == dict:
                ...
            elif type(portfolio) == pd.DataFrame:
                var_df = pd.DataFrame(var_array, columns=['Day', 'VaR'])
            elif type(portfolio) == pyspark.sql.DataFrame:
                var_df = pyspark.sql.DataFrame
            return var_df

    def refresh_data(
            self,
            ticker: str,
            start: dt.datetime = dt.date.today(),
            end: dt.datetime = dt.date.today(),
    ):
        """
        Using the MongoDB Atlas database, we search for a given ticker
        and return the data needed to create a chart in pyChartJS.
        :param ticker: Stocker ticker (string)
        :param start: Get the stock closing price on or after the given date
        :param end: Get the stock closing price on or before the given date
        :return: Sentiment chart object with new data
        """

        stock_data = retrieve_company_stock_price_from_mongo(ticker)[["Date", "Close"]]
        index_data = retrieve_company_stock_price_from_mongo("SPY")[["Date", "Close"]]
        stock_data, index_data = (
            self._transformer(stock_data).dropna(),
            self._transformer(index_data).dropna(),
        )
        self.data = pf.show_perf_stats(stock_data, index_data)
        return self

    def create_chart(self):
        self.chart = None
        return self

    def display_chart(self):
        return


if __name__ == "__main__":
    chart = VaR_Chart()
    chart.calculate_VaR(chart.test_portfolio('pandas'))
    print(chart.test_portfolio())
    # chart = chart.refresh_data("SPY", dt.date(2021, 10, 10))
    print(chart.data)
