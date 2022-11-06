import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from src.utils import generate_line_graph

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

dash.register_page(__name__, order=6)

layout = html.Div(
    children=[
        html.P(
            children="This is our Account page for editing the application credentials."
        )
    ]
)
