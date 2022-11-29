import datetime as dt

import dash
import dash_bootstrap_components as dbc
import diskcache
from dash import html, dcc, callback, Input, Output, DiskcacheManager

from src.analysis.market import get_tickers, get_kdj_data, kdjChart, movingAvgChart

from src.analysis.sentiment_analysis import (
    reddit_chart,
    twitter_counts,
    twitter_searches,
)

cache = diskcache.Cache("../cache")
background_callback_manager = DiskcacheManager(cache)

dash.register_page(__name__, order=3)
layout = html.Div()
tickers = get_tickers()

start = dt.datetime(2022, 1, 1).date()
end = dt.datetime.today().date()

layout = html.Div(
    children=[
        dbc.Row(
            children=[
                dbc.Col(html.H3(children="Analysis"), width=2),
                dbc.Col(
                    dcc.Checklist(["Refresh Data"], id="data_refresh"),
                    align="center",
                    width=2,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        tickers,
                        "GOOG",  # Initialize the dropdown menu with Google ticker
                        id="tickers",
                        searchable=True,
                    ),
                    align="center",
                    width=2,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        ["wma_7", "wma_30", "wma_60", "wma_120"],
                        "wma_7",
                        id="wma",
                        searchable=False,
                    ),
                    align="center",
                    width=2,
                ),
                dbc.Col(
                    dcc.DatePickerRange(
                        start_date=start,
                        end_date=end,
                        id="analysis_dates",
                        display_format="MMM DD, Y",
                        with_full_screen_portal=False,
                        with_portal=True,
                        updatemode="bothdates",
                    ),
                    align="center",
                ),
            ],
            justify="between",
        ),
        dbc.Row(
            children=[
                dbc.Col(children=[dcc.Graph(id="invest_chart")], width=3),
                dbc.Col(children=[dcc.Graph(id="stocks_chart")], width=3),
                dbc.Col(children=[dcc.Graph(id="wsb_chart")], width=3),
                dbc.Col(children=[dcc.Graph(id="twitter_search")], width=3),
            ],
            className="g-0",
        ),
        dbc.Row(
            children=[
                dbc.Col(children=[dcc.Graph(id="twitter_count")]),
            ]
        ),
        dbc.Row(
            children=[
                dbc.Col(children=[dcc.Graph(id="kdj_chart")]),
            ]
        ),
        dbc.Row(children=[dcc.Graph(id="wma_chart")]),
    ]
)


@callback(
    Output(component_id="kdj_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    Input(component_id="analysis_dates", component_property="start_date"),
    Input(component_id="analysis_dates", component_property="end_date"),
    background=True,
    manager=background_callback_manager,
)
def update_kdj(ticker, start_date, end_date):
    kdj = get_kdj_data(ticker, start_date, end_date)
    return kdjChart(ticker, kdj).create_chart()


@callback(
    Output(component_id="twitter_count", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    background=True,
    manager=background_callback_manager,
)
def count_tweets(ticker):
    tweet_counts = twitter_counts(query=ticker)
    return tweet_counts.create_chart()


@callback(
    Output(component_id="twitter_search", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    background=True,
    manager=background_callback_manager,
)
def twitter_sentiment(ticker):
    twitter_search = twitter_searches(query=ticker)
    return twitter_search.create_chart()


@callback(
    Output(component_id="wsb_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    background=True,
    manager=background_callback_manager,
)
def r_wsb_sentiment(ticker):
    sub = "wallstreetbets"
    reddit_search = reddit_chart(ticker, sub)
    return reddit_search.create_chart()


@callback(
    Output(component_id="stocks_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    background=True,
    manager=background_callback_manager,
)
def r_stocks_sentiment(ticker):
    sub = "stocks"
    reddit_search = reddit_chart(ticker, sub)
    return reddit_search.create_chart()


@callback(
    Output(component_id="invest_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    background=True,
    manager=background_callback_manager,
)
def r_investing_sentiment(ticker):
    sub = "investing"
    reddit_search = reddit_chart(ticker, sub)
    return reddit_search.create_chart()


@callback(
    Output(component_id="wma_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    Input(component_id="wma", component_property="value"),
    Input(component_id="analysis_dates", component_property="start_date"),
    Input(component_id="analysis_dates", component_property="end_date"),
    background=True,
    manager=background_callback_manager,
)
def update_wma(ticker, wma, start_date, end_date):
    return movingAvgChart(ticker).createWMA(wma, start_date, end_date)
