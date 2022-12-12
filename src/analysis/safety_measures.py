from functools import cache
from typing import Union
from src.data.yahoo import retrieve_company_stock_price_from_mongo
import plotly.graph_objects as go

import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
import pyfolio as pf
from src.analysis.market import transform_dates

from scipy.stats import norm
from pathlib import Path


@cache
def create_portfolio_df(
    file_location: str = f"{str(Path(__file__).parents[1])}/test_portfolio.csv",
):
    """
    Takes a file location and creates a standardized Pandas portfolio.
    :param file_location: string path to portfolio added to the dashboard.
    :return: Returns a pandas dataframe with a test portfolio.
    """
    portfolio = pd.read_csv(file_location, header=0)

    portfolio = portfolio.rename(columns={"Price": "Close", "Symbol": "Ticker"})
    portfolio = portfolio.replace(r"$", "", regex=True).replace(r",", "", regex=True)
    portfolio["total_cost"] = (
        portfolio["Close"].astype(float).values
        * portfolio["Share"].astype(float).values
    )
    denominator = float(portfolio["total_cost"].sum())
    portfolio["Weight"] = np.round(
        portfolio.Close.astype(float).values / denominator, 3
    )
    portfolio = (
        portfolio.dropna()
    )  # Drops a stock from the portfolio if the weight is NaN

    return portfolio


def calculate_VaR(
    start_date: str,
    end_date: str,
    portfolio: pd.DataFrame,
    initial_investment: Union[float, int] = 0,
    conf_level: Union[float, int] = 0.05,
):
    """
    Calculates the Value at Risk overtime.
    Retrieved from https://www.interviewqs.com/blog/value-at-risk

    :param start_date: String date to start the value at risk chart.
    :param end_date: String date to end the value at risk chart.
    :param portfolio: Sample data or data uploaded by participants.
    :param initial_investment:
    :param conf_level: equal to alpha (a). Typically set to 95% or 1 - .05 (a).

    :return Value at Risk: dataframe containing the daily value at risk.
    """

    # If no portfolio data is given, we'll represent no data as no investments.
    # Given no investments, there's no value at risk.

    if portfolio is not None:
        returns = pd.DataFrame()
        costs = []
        shares = []
        weights = []
        tickers = portfolio["Ticker"].values

        start_date, end_date = transform_dates(start_date=start_date, end_date=end_date)

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
                    (mongo_data["Date"] >= start_date.date())
                    & (mongo_data["Date"] <= end_date.date())
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
    if initial_investment == 0:
        initial_investment = np.dot(costs, shares)
    weights = np.array(
        weights
    )  # Create an array for the list object to perform the remaining calculations
    cov_matrix = returns.cov(numeric_only=True)  # Used to calculate mean and standard deviation below
    avg_rets = np.mean(returns)  # Calculate mean returns for each stock

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
    """
    Create safety first ratio that is used to define the risk involved with a
    given portfolio. If the value is negative, the returns are below the expected
    value, and there may be a portfolio that'd meet the user's expectation better.

    :param portfolio: Dataframe containing data about the
    :param returns_type:
    :param exp_return:
    :param start_date:
    :param end_date:
    :return:
    """
    returns = pd.DataFrame()
    tickers = list(portfolio["Ticker"].values)
    start_date, end_date = transform_dates(start_date=start_date, end_date=end_date)

    # Iterate through the tickers in the portfolio after transforming the portfolio to Pandas
    for ticker in tickers:
        mongo_data = retrieve_company_stock_price_from_mongo(ticker)

        if mongo_data.isna().values.all():
            mongo_data = yf.Ticker(ticker).history("max").reset_index()

        if not mongo_data.empty:
            mongo_data["Date"] = pd.to_datetime(mongo_data["Date"]).dt.date
            mongo_data = mongo_data[
                (mongo_data["Date"] >= start_date.date())
                & (mongo_data["Date"] <= end_date.date())
            ]
            mongo_data["Close"] = mongo_data["Close"].replace("$", "")
            transformed = mongo_data.rename({"Close": ticker}, axis=1)[["Date", ticker]]
            if returns.empty:
                returns = transformed
            else:
                returns = returns.merge(transformed, on="Date", how="inner")

    returns = np.sum(returns, axis=1)
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
    def __init__(self, data: pd.DataFrame):
        self.chart = None
        self.data = data

    def create_chart(self):
        fig = go.Figure(
            go.Indicator(
                mode="number+delta",
                value=self.data.VaR.iat[-1],
                delta={"reference": self.data.VaR.iat[-2], "valueformat": "$,.0f"},
                title={"text": "Current Portfolio Value at Risk"},
                domain={"y": [0, 1], "x": [0.25, 0.75]},
                number={"valueformat": "$,.0f"},
            )
        )

        fig.update_traces(
            delta_increasing_color="#FF4136",
            delta_decreasing_color="#3D9970",
            selector=dict(type="indicator"),
        )

        fig.add_trace(go.Scatter(y=self.data.VaR.values, name='Value at Risk'))

        fig.update_layout(
            {
                "title": {
                    "text": f"Value at Risk Over Time<br><sup>Over time, your portfolio has grown, and today, the value at risk is ${self.data.VaR.iat[-1]},<br>which is ${round(self.data.VaR.iat[-1] - self.data.VaR.iat[-2], 2)} more than yesterday.</sup>",
                    "font": {"color": "White"},
                }
            },
            yaxis_tickprefix="$",
            yaxis_tickformat=",.0f",
            yaxis_color="White",
            paper_bgcolor="#060606",
            plot_bgcolor="#060606",
            xaxis_color="White",
            yaxis_title={"text": "Value at Risk"},
            xaxis_title={"text": "Days between Date Range"},
            font={"color": "White"},
            xaxis={"showgrid": False},
            yaxis={"showgrid": False},
        )

        self.chart = fig
        return self.chart


class SFR_Chart:
    def __init__(self, sfr: str):
        self.chart = None
        self.sfr = sfr

    def create_chart(self):
        fig = go.Figure(
            go.Indicator(
                mode="number",
                value=self.sfr,
                title={"text": "Portfolio Safety First Ratio"},
                number={"valueformat": ".2f"},
                domain={"x": [0, 1], "y": [0, 1]},
            )
        )

        fig.update_layout(
            width=300, height=300, paper_bgcolor="#060606", font={"color": "White"}
        )

        self.chart = fig
        return self.chart
