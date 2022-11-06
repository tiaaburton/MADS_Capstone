import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from src.utils import generate_line_graph

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# Imported charts from the
from src.analysis.sentiment_analysis import reddit_chart
test_query = 'GOOG'
test_subs = 'wallstreetbets+stocks+investing'
reddit_search = reddit_chart(test_query, test_subs)
reddit_indicator = reddit_search.create_chart()

dash.register_page(__name__, path="/analysis", order=3)

layout = html.Div(
    [
        dbc.Row(dbc.Col(html.H1(children="Analysis"))),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='reddit_indicator', figure=reddit_indicator), width=3),
                dbc.Col(html.Div("One of three columns"), width=3),
                dbc.Col(html.Div("One of three columns")),
            ]
        ),
    ]
)