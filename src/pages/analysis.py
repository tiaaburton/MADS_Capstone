import datetime as dt

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

from src.analysis.market import get_tickers, get_kdj_data, kdjChart, movingAvgChart

from src.analysis.sentiment_analysis import (
    reddit_chart,
    twitter_counts,
    twitter_searches,
)

dash.register_page(__name__, order=3)

FILTER_STYLE = {
    "background-color": "#005999",
    "color": "white",
    "font-size": "14px",
    "text-align": "right",
    "right": 0,
}

DROPDOWN_STYLE = {
    "background-color": "#005999",
    "color": "gray",
    "font-size": "12px",
    "margin": "5px",
    "text-align": "left",
}

tickers = get_tickers()
start = dt.datetime(2022, 9, 1).date()
end = dt.datetime.today().date()

layout = html.Div(
    children=[
        dbc.Row(
            children=[
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
                        style=DROPDOWN_STYLE,
                    ),
                    align="center",
                    width=2,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        options=[
                            {"label": ma.replace("_", " ").upper(), "value": ma}
                            for ma in ["wma_7", "wma_30", "wma_60", "wma_120"]
                        ],
                        value="wma_7",
                        id="wma",
                        searchable=False,
                        style=DROPDOWN_STYLE,
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
            style=FILTER_STYLE,
            className="g-0",
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
                dbc.Col(children=[
                    dcc.Dropdown(
                        options=['Weighted Moving Average', 'KDJ Indicator'],
                        value='Weighted Moving Average',
                        id='indicator_selector'
                    ),
                    dcc.Graph(id='indicator_chart')
                ])
            ]
        ),
    ]
)



@callback(
    Output(component_id="twitter_count", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    background=True,
)
def count_tweets(ticker):
    tweet_counts = twitter_counts(query=ticker)
    return tweet_counts.create_chart()


@callback(
    Output(component_id="twitter_search", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    Input(component_id="data_refresh", component_property="value"),
    background=True,
)
def twitter_sentiment(ticker, checkbox):
    twitter_search = twitter_searches(query=ticker)
    if checkbox is None or len(checkbox) == 0:
        return twitter_search.create_chart()
    elif checkbox[0] == "Refresh Data":
        return twitter_search.create_chart(True, 3)


@callback(
    Output(component_id="wsb_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    Input(component_id="data_refresh", component_property="value"),
    background=True,
)
def r_wsb_sentiment(ticker, checkbox):
    sub = "wallstreetbets"
    reddit_search = reddit_chart(ticker, sub)
    if checkbox is None or len(checkbox) == 0:
        return reddit_search.create_chart()
    elif checkbox[0] == "Refresh Data":
        return reddit_search.create_chart(True)


@callback(
    Output(component_id="stocks_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    Input(component_id="data_refresh", component_property="value"),
    background=True,
)
def r_stocks_sentiment(ticker, checkbox):
    sub = "stocks"
    reddit_search = reddit_chart(ticker, sub)
    if checkbox is None or len(checkbox) == 0:
        return reddit_search.create_chart()
    elif checkbox[0] == "Refresh Data":
        return reddit_search.create_chart(True)


@callback(
    Output(component_id="invest_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    Input(component_id="data_refresh", component_property="value"),
    background=True,
)
def r_investing_sentiment(ticker, checkbox):
    sub = "investing"
    reddit_search = reddit_chart(ticker, sub)
    if checkbox is None or len(checkbox) == 0:
        return reddit_search.create_chart()
    elif checkbox[0] == "Refresh Data":
        return reddit_search.create_chart(True)


@callback(
    Output(component_id="indicator_chart", component_property="figure"),
    Input(component_id="tickers", component_property="value"),
    Input(component_id="wma", component_property="value"),
    Input(component_id="indicator_selector", component_property="value"),
    Input(component_id="analysis_dates", component_property="start_date"),
    Input(component_id="analysis_dates", component_property="end_date"),
    background=True,
)
def update_wma(ticker, wma, indicator, start_date, end_date):
    if indicator == 'Weighted Moving Average':
        return movingAvgChart(ticker).createWMA(wma, start_date, end_date)
    elif indicator == 'KDJ Indicator':
        kdj = get_kdj_data(ticker, start_date, end_date)
        return kdjChart(ticker, kdj).create_chart()
