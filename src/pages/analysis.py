from pathlib import Path

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from src.utils import generate_line_graph

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# Importing analytical charts
from src.analysis.sentiment_analysis import (
    reddit_chart,
    twitter_counts,
    twitter_searches,
)

# Prime the charts with an initial search before loading
# into the dashboard
test_query = "GOOG"
test_subs = "wallstreetbets+stocks+investing"
reddit_search = reddit_chart(test_query, test_subs)
reddit_indicator = reddit_search.create_chart()

tweet_counts = twitter_counts(query=test_query)
twitter_count_ind = tweet_counts.create_chart()

twitter_search = twitter_searches(query=test_query)
twitter_search_ind = twitter_search.create_chart()

dash.register_page(__name__, order=3)

layout = html.Div(
    [
        dbc.Row(
            children=[
                dbc.Col(html.H3(children="Analysis")),
                        dbc.Col(
                            children=[
                                dcc.Input(
                                    id="reddit_subs",
                                    value=test_query,
                                    type='text',
                                    style={"width": "20%", },
                                    placeholder="Enter a ticker symbol to search social media.",
                                    rows=1,

                                ),
                                html.Button("Submit", id="reddit_subs_button")
                            ]
                        ),
            ],
            #     align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    children=[dcc.Graph(id="reddit_sentiment", figure=reddit_indicator)]
                ),
                dbc.Col(
                    children=[dcc.Graph(id="twitter_search", figure=twitter_search_ind)]
                ),
            ]
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(id="twitter_count", figure=twitter_count_ind)),
        ),
    ]
)

# @callback(
#     Output(component_id='my-output', component_property='children'),
#     Input(component_id='reddit_subs', component_property='value')
# )
# def update_output_div(input_value):
#     return f'Output: {input_value}'
