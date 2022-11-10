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
from src.analysis.safety_measures import VaR_Chart, SFR_Chart

dash.register_page(__name__, order=3)

# Prime the charts with an initial search before loading
# into the dashboard
test_query = "GOOG"
test_subs = "wallstreetbets+stocks+investing"
reddit_search = reddit_chart(test_query, test_subs)
reddit_indicator = reddit_search.create_chart()

# tweet_counts = twitter_counts(test_query)
# twitter_count_ind = tweet_counts.create_chart()

# twitter_search = twitter_searches()
# twitter_search.search_n_times(4, test_query)
# twitter_search_ind = twitter_search.create_chart()

layout = html.Div(
    [
        dbc.Row(
            children=[
                dbc.Col(html.H3(children="Analysis")),
                dbc.Col(
                    children=[
                        dcc.Textarea(
                            "reddit_subs",
                            value=test_query,
                            style={"width": "20%"},
                            placeholder="Enter a ticker symbol to search social media.",
                            rows=1,
                        ),
                        html.Button("Submit", id="reddit_subs_button", n_clicks=0),
                    ]
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="reddit_indicator", figure=reddit_indicator)),
                # dbc.Col(dcc.Graph(id='twitter_count_ind', figure=twitter_count_ind)),
                # dbc.Col(dcc.Graph(id='twitter_search_ind', figure=twitter_search_ind)),
            ]
        ),
    ]
)
