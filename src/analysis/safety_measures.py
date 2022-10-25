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


class VaR_Chart:
    def __init__(self):
        self.data = None
        self.chart = None

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
            if 'value' in portfolio[stock]:
                portfolio_value += portfolio[stock]['value']

        for stock in portfolio_stocks:
            if 'value' in portfolio[stock]:
                stock_weight = portfolio[stock]['value'] / portfolio_value
                portfolio[stock]['weight'] = round(stock_weight, 3)

        assert (np.isclose([round(sum([portfolio[stock]['weight'] for stock in portfolio_stocks
                                       if 'weight' in portfolio[stock]]), 2)], [1.0]) == True).all()

        return portfolio

    @staticmethod
    def _transformer(data, start: dt.datetime = dt.date.today(), end: dt.datetime = dt.date.today()):
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        data = data[(data['Date'] >= start) & (data['Date'] <= end)]
        data['Close'] = data['Close'].pct_change()
        return data

    def calculate_VaR(self,
                      portfolio=dict[str, dict],
                      index: str = 'SPY',
                      start: dt.datetime = dt.date.today(),
                      end: dt.datetime = dt.date.today(),
                      initial_investment: Union[float, int] = 0,
                      num_days: int = 0):
        """
        Calculates the Value at Risk overtime.
        Retrieved from https://www.interviewqs.com/blog/value-at-risk

        Return:
            Value at Risk: value or dataframe
        """
        portfolio_stocks = list(portfolio.keys())
        returns = pd.DataFrame(columns=['Date', 'Close'])
        weights = []

        for stock in portfolio_stocks:
            port_data = portfolio[stock]
            stock_data = None

            # try:
            stock_data = retrieve_company_stock_price_from_mongo(stock)[['Date', 'Close']]
            # except:
            #     continue

            if stock_data is not None:
                ret = self._transformer(stock_data, start, end)
                weights.append(port_data['weight'])
                returns.join(ret, on='Date', how='outer')

        cov_matrix = returns.cov()

        # Calculate mean returns for each stock
        avg_rets = returns.mean()

        # Calculate mean returns for portfolio overall, using mean, using dot product formula to
        # normalize against investment weights
        port_mean = avg_rets.dot(weights)

        # Calculate portfolio standard deviation
        port_stdev = np.sqrt(weights.T.dot(cov_matrix).dot(weights))

        # Calculate mean of given investment
        mean_investment = (1 + port_mean) * initial_investment

        # Calculate standard deviation of given investment
        stdev_investment = initial_investment * port_stdev

        # Select our confidence interval (I'll choose 95% here)
        conf_level1 = 0.05

        # Using SciPy ppf method to generate values for the inverse cumulative distribution function to a normal
        # distribution. Plugging in the mean, standard deviation of our portfolio as calculated above
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
        cutoff1 = norm.ppf(conf_level1, mean_investment, stdev_investment)

        # Finally, we can calculate the VaR at our confidence interval
        var_1d1 = initial_investment - cutoff1

        if num_days == 0:
            return var_1d1

        # Calculate n Day VaR
        else:
            var_array = [(0, var_1d1)]
            num_days = int(15)
            for x in range(1, num_days + 1):
                varOnDay = np.round(var_1d1 * np.sqrt(x), 2)
                var_array.append((x, varOnDay))
                print(str(x) + " day VaR @ 95% confidence: " + str(np.round(var_1d1 * np.sqrt(x), 2)))

            return var_1d1

    def refresh_data(self, ticker: str, start: dt.datetime = dt.date.today(), end: dt.datetime = dt.date.today()):
        """
        Using the MongoDB Atlas database, we search for a given ticker
        and return the data needed to create a chart in pyChartJS.
        :param ticker: Stocker ticker (string)
        :param start: Get the stock closing price on or after the given date
        :param end: Get the stock closing price on or before the given date
        :return: Sentiment chart object with new data
        """

        stock_data = retrieve_company_stock_price_from_mongo(ticker)[['Date', 'Close']]
        index_data = retrieve_company_stock_price_from_mongo('SPY')[['Date', 'Close']]
        stock_data, index_data = self._transformer(stock_data).dropna(), self._transformer(index_data).dropna()
        self.data = pf.show_perf_stats(stock_data, index_data)
        return self

    def create_chart(self):
        self.chart = None
        return self

    def display_chart(self):
        return


if __name__ == '__main__':
    chart = VaR_Chart()
    chart = chart.refresh_data('SPY', dt.date(2021, 10, 10))
    print(chart.data)
