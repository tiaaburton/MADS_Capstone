from typing import Union
from scipy.stats import norm
from src.data.yahoo import retrieve_company_stock_price_from_mongo
import plotly.graph_objects as go
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
from pathlib import Path


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

    return portfolio


def test_portfolio(
    test_file: str = f"{str(Path(__file__).parents[4])}/Downloads/test_portfolio.csv",
):
    """
    Sample portfolio used to complete functions. Will replace in analysis page with
    portfolio data.

    :return: Returns a pandas dataframe with a test portfolio.
    """
    portfolio = pd.read_csv(test_file, header=0)

    portfolio = portfolio.rename(columns={"Price": "Close", "Symbol": "Ticker"})
    portfolio = portfolio.replace(r"$", "", regex=True).replace(r",", "", regex=True)
    portfolio["total_cost"] = (
        portfolio["Close"].astype(float).values
        * portfolio["Share"].astype(float).values
    )
    denonimator = float(portfolio["total_cost"].sum())
    portfolio["Weight"] = np.round(
        portfolio.Close.astype(float).values / denonimator, 3
    )
    portfolio = (
        portfolio.dropna()
    )  # Drops a stock from the portfolio if the weight is NaN

    return portfolio


def calculate_VaR(
    portfolio: Union[None, dict[str, dict], pd.DataFrame],
    initial_investment: Union[float, int] = 0,
    start_date: Union[dt.datetime, dt.date] = dt.date.today(),
    end_date: Union[dt.datetime, dt.date] = dt.date.today(),
    conf_level: Union[float, int] = 0.05,
):
    """
    Calculates the Value at Risk overtime.
    Retrieved from https://www.interviewqs.com/blog/value-at-risk

    Return:
        Value at Risk: value or dataframe
    """

    # If no portfolio data is given, we'll represent no data as no investments.
    # Given no investments, there's no value at risk.
    if portfolio is None:
        return 0.0

    if initial_investment == 0 and portfolio is not None:
        if type(portfolio) == dict:
            ...

        returns = pd.DataFrame()
        costs = []
        shares = []
        weights = []
        tickers = portfolio["Ticker"].values

        # Iterate through the tickers in the portfolio after transforming the portfolio to Pandas
        for ticker in tickers:
            mongo_data = retrieve_company_stock_price_from_mongo(ticker)
            if mongo_data.isna().values.all():
                mongo_data = yf.Ticker(ticker).history("max").reset_index()
            if not mongo_data.empty:
                shares.append(
                    int(portfolio[portfolio["Ticker"] == ticker]["Share"].values[0])
                )
                costs.append(
                    float(portfolio[portfolio["Ticker"] == ticker]["Cost"].values[0])
                )
                weights.append(
                    portfolio[portfolio["Ticker"] == ticker]["Weight"].values[0]
                )

                mongo_data["Date"] = pd.to_datetime(mongo_data["Date"]).dt.date
                mongo_data = mongo_data[
                    (mongo_data["Date"] >= start_date)
                    & (mongo_data["Date"] <= end_date)
                ]
                mongo_data["Close"] = mongo_data["Close"].replace("$", "").pct_change()
                transformed = mongo_data.rename({"Close": ticker}, axis=1)[
                    ["Date", ticker]
                ]
                if returns.empty:
                    returns = transformed
                else:
                    returns = returns.merge(transformed, on="Date", how="inner")

    returns.fillna(0.0, inplace=True)
    initial_investment = np.dot(costs, shares)
    weights = np.array(
        weights
    )  # Create an array for the list object to perform the remaining calculations
    cov_matrix = returns.cov()  # Used to calculate mean and standard deviation below
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
    num_days = (end_date - start_date).days
    # print(start-end, (start - end).days, (end - start).days)
    if num_days == 0:
        var_df = pd.DataFrame([[0, var_1d1]], columns=["Day", "VaR"])

    # Calculate n Day VaR with 95% confidence level if date diff > 0
    else:
        var_array = [(0, var_1d1)]
        for x in range(1, num_days + 1):
            varOnDay = np.round(var_1d1 * np.sqrt(x), 2)
            var_array.append((x, varOnDay))
        var_df = pd.DataFrame(var_array, columns=["Day", "VaR"])

    var_df.fillna(0.0, inplace=True)

    return var_df


def calculate_SFR(
    portfolio: pd.DataFrame,
    returns_type: Union["daily", "weekly", "monthly", "yearly"] = "daily",
    exp_return: Union[int, float] = 0.0,
    start_date: Union[dt.datetime, dt.date] = dt.date.today(),
    end_date: Union[dt.datetime, dt.date] = dt.date.today(),
):
    if portfolio is None:
        return 0.0

    else:
        if type(portfolio) == dict:
            ...

        returns = pd.DataFrame()
        tickers = portfolio["Ticker"].values

        # Iterate through the tickers in the portfolio after transforming the portfolio to Pandas
        for ticker in tickers:
            mongo_data = retrieve_company_stock_price_from_mongo(ticker)

            if mongo_data.isna().values.all():
                mongo_data = yf.Ticker(ticker).history("max").reset_index()

            if not mongo_data.empty:
                mongo_data["Date"] = pd.to_datetime(mongo_data["Date"]).dt.date
                mongo_data = mongo_data[
                    (mongo_data["Date"] >= start_date)
                    & (mongo_data["Date"] <= end_date)
                ]
                mongo_data["Close"] = mongo_data["Close"].replace("$", "")
                transformed = mongo_data.rename({"Close": ticker}, axis=1)[
                    ["Date", ticker]
                ]
                if returns.empty:
                    returns = transformed
                else:
                    returns = returns.merge(transformed, on="Date", how="inner")

        returns = returns.sum(axis=1)
        returns = returns.pct_change()

        if returns_type != "daily":
            returns = pf.timeseries.aggregate_returns(returns, returns_type)

        returns.fillna(0.0, inplace=True)

        avg_ret = np.average(returns)
        ret_stdv = np.std(returns)
        SFR = (avg_ret - exp_return) / ret_stdv

        # The function will return 0.0 if the denominator is 0.0
        if ret_stdv == 0.0 or np.isnan(SFR):
            return 0.0
        else:
            return np.round(SFR, 3)


class VaR_Chart:
    def __init__(self):
        self.chart = None

    def create_chart(self, data):
        fig = go.Figure(
            go.Indicator(
                mode="number+delta",
                value=data.VaR.iat[-1],
                delta={"reference": data.VaR.mean(), "valueformat": "$,.0f"},
                title={"text": "Value at Risk for Portfolio"},
                domain={"y": [0, 1], "x": [0.25, 0.75]},
                number={"valueformat": "$,.0f"},
            )
        )

        fig.update_traces(
            delta_increasing_color="#FF4136",
            delta_decreasing_color="#3D9970",
            selector=dict(type="indicator"),
        )

        fig.add_trace(go.Scatter(y=data.VaR.values))

        fig.update_layout(
            xaxis={"range": [0, 62]}, yaxis_tickprefix="$", yaxis_tickformat=",.0f"
        )

        self.chart = fig
        return self.chart


class SFR_Chart:
    def __init__(self):
        self.chart = None

    def create_chart(self, sfr):
        fig = go.Figure(
            go.Indicator(
                mode="number",
                value=sfr,
                title={"text": "Portfolio Safety First Ratio"},
                domain={"y": [0, 1], "x": [0.25, 0.75]},
                number={"valueformat": ".2f"},
            )
        )

        self.chart = fig
        return self.chart


if __name__ == "__main__":
    p_str = f"{str(Path(__file__).parents[4])}/Downloads/test_portfolio2.csv"
    start = dt.datetime(2022, 1, 1).date()
    end = dt.datetime.today().date()
    p = test_portfolio(p_str)
    var = calculate_VaR(p, start_date=start, end_date=end)
    VaR_Chart().create_chart(var).show()

    sfr = calculate_SFR(p, exp_return=2, start_date=start, end_date=end)
    SFR_Chart().create_chart(sfr).show()
