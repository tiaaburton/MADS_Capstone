import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from yfinance.utils import get_json

from pathlib import Path
from functools import cache


@cache
def get_portfolio_data(
    file_name: str = f"{str(Path(__file__).parents[1])}/test_portfolio.csv",
):
    """
    Create a dataframe for an uploaded portfolio. Add new column names and
    transform some data.

    :param file_name: Dynamic absolute path to CSV file
    :return: Pandas Dataframe with portfolio data
    """
    portfolio = pd.read_csv(file_name)
    tickers = list(portfolio.Symbol.values)
    portfolio["Sector"] = portfolio["Symbol"].apply(
        lambda ticker: get_json(f"https://finance.yahoo.com/quote/{ticker}")[
            "summaryProfile"
        ]["sector"]
    )
    portfolio["Price"] = portfolio["Symbol"].apply(
        lambda ticker: get_json(f"https://finance.yahoo.com/quote/{ticker}")["price"][
            "regularMarketPrice"
        ]
    )
    denominator = (portfolio["Price"].values * portfolio["Share"].values).sum()
    portfolio["Weight"] = np.round_(
        (portfolio["Price"].values * portfolio["Share"].values) / denominator, 2
    )
    portfolio["P/L"] = np.round_(
        (portfolio["Price"].values - portfolio["Cost"].values)
        / portfolio["Cost"].values,
        2,
    )
    return portfolio


class portfolioCharts:
    def __init__(self):
        self.data = get_portfolio_data()
        self.worth_chart = None
        self.worth_table = None
        self.changes_chart = None
        self.sector_chart = None

    def update_portfolio(self, new_portfolio: str):
        """
        Update the initial portfolio string used. This allows for dynamic
        switching between portfolios uploaded into Market Shopper.

        :param new_portfolio: Absolute path string to new CSV portfolio
        :return: Saves new data to existing portfolio charts object
        """
        self.data = get_portfolio_data(new_portfolio)
        return self

    def create_worth_chart(self):
        """
        Create a chart that shows the portion of the portfolio in
        its designated sector and the stocks.

        :return: Plotly bar chart
        """
        fig = px.bar(
            self.data,
            x="Sector",
            y="Weight",
            color="Symbol",
            text="Symbol",
            title="Portfolio Distribution by Sector",
        )
        fig.update_layout(
            paper_bgcolor="#060606",
            plot_bgcolor="#060606",
            font={"color": "White"},
            showlegend=False,
            yaxis={"tickformat": ",.0%", "range": [0, 1], "showgrid": False},
            xaxis={"showgrid": False},
        )
        self.worth_chart = fig
        return self.worth_chart

    def create_worth_table(self):
        """
        Create a table with portfolio data.

        :return: Plotly table
        """
        fig = go.Figure()

        headerColor = "grey"
        rowEvenColor = "lightgrey"
        rowOddColor = "white"

        fig.add_trace(
            go.Table(
                header=dict(
                    values=[f"<b>{col}</b>" for col in list(self.data.columns)],
                    line_color="#005999",
                    fill_color="#005999",
                    align=["center"],
                    font=dict(color="white", size=12),
                ),
                cells=dict(
                    values=list(self.data.transpose().values),
                    line_color="#060606",
                    # 2-D list of colors for alternating rows
                    fill_color=["#060606"],
                    align=["center"],
                    font=dict(color="white", size=11),
                )
            )
        )
        fig.update_layout(paper_bgcolor="#060606")
        fig.update_traces(columnwidth=3, selector=dict(type='table'))
        self.worth_table = fig
        return self.worth_table

    def create_changes_chart(self):
        changes = self.data.copy(deep=True)
        changes.dropna(inplace=True)
        changes["Color"] = np.where(changes["P/L"] < 0, "red", "green")
        fig = go.Figure(
            go.Bar(
                x=changes["P/L"],
                y=changes["Symbol"],
                orientation="h",
                text=changes["P/L"],
            )
        )
        fig.update_layout(
            showlegend=False,
            paper_bgcolor="#060606",
            plot_bgcolor="#060606",
            yaxis={"categoryorder": "total ascending", "showgrid": False},
            font={"color": "White"},
            xaxis={"showgrid": False},
            title_text="Portfolio Profit & Loss<br><sup>Compares the stock's latest price to the cost when bought.</sup>",
        )
        fig.update_traces(
            marker_color=changes["Color"],
        )
        self.changes_chart = fig
        return self.changes_chart

    def create_sector_chart(self):
        sector_data = self.data.groupby("Sector")["Weight"].agg("sum")
        sector_data = sector_data.reset_index()

        fig = go.Figure()
        fig.add_trace(
            go.Pie(
                labels=sector_data["Sector"],
                values=sector_data["Weight"],
            )
        )
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(
            title_text="Portfolio Distribution by Sector",
            showlegend=False,
            paper_bgcolor="#060606",
            font={"color": "White"},
            yaxis={"categoryorder": "total ascending"},
        )
        self.sector_chart = fig
        return self.sector_chart


if __name__ == "__main__":
    charts = portfolioCharts()
    # charts.create_sector_chart().show()
    # charts.create_worth_table().show()
    # charts.create_worth_chart().show()
    charts.create_changes_chart().show()
