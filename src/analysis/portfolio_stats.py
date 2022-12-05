import datetime as dt
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

    def create_worth_chart(self):
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
        fig = go.Figure()

        headerColor = "grey"
        rowEvenColor = "lightgrey"
        rowOddColor = "white"

        fig.add_trace(
            go.Table(
                header=dict(
                    values=[f"<b>{col}</b>" for col in list(self.data.columns)],
                    line_color="darkslategray",
                    fill_color=headerColor,
                    align=["center"],
                    font=dict(color="white", size=12),
                ),
                cells=dict(
                    values=list(self.data.transpose().values),
                    line_color="darkslategray",
                    # 2-D list of colors for alternating rows
                    fill_color=[
                        [
                            rowOddColor,
                            rowEvenColor,
                            rowOddColor,
                            rowEvenColor,
                            rowOddColor,
                        ]
                        * len(self.data)
                    ],
                    align=["center"],
                    font=dict(color="darkslategray", size=11),
                ),
            )
        )
        fig.update_layout(paper_bgcolor="#060606")
        self.worth_table = fig
        return self.worth_table

    def create_changes_chart(self):
        changes = self.data.copy()
        changes["Color"] = np.where(changes["P/L"] < 0, "red", "green")
        fig = px.bar(
            changes,
            x="P/L",
            y="Symbol",
            title="Portfolio Profit & Loss<br><sup>Compares the stock's latest price to the cost when bought.</sup>",
            text="P/L",
            orientation="h",
        )
        fig.update_layout(
            showlegend=False,
            paper_bgcolor="#060606",
            plot_bgcolor="#060606",
            yaxis={"categoryorder": "total ascending", "showgrid": False},
            font={"color": "White"},
            xaxis={"showgrid": False},
        )
        fig.update_traces(marker_color=changes["Color"])
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
                hole=0.3,
                title="Portfolio Distribution by Sector",
            )
        )
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(
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
