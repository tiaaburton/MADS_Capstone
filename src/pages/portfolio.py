from pathlib import Path

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from src.utils import generate_line_graph
import datetime as dt

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

from src.analysis.safety_measures import (
    test_portfolio,
    VaR_Chart,
    SFR_Chart,
    calculate_SFR,
    calculate_VaR,
)

p_str = f"{str(Path(__file__).parents[1])}/test_portfolio.csv"
start = dt.datetime(2022, 1, 1).date()
end = dt.datetime.today().date()
p = test_portfolio(p_str)
var = calculate_VaR(p, start_date=start, end_date=end)
var_chart = VaR_Chart().create_chart(var)

sfr = calculate_SFR(p, exp_return=0.02, start_date=start, end_date=end)
sfr_chart = SFR_Chart().create_chart(sfr)

dash.register_page(__name__, order=2)

layout = html.Div(
    children=[
        dbc.Row(
            children=[
                dbc.Col(html.H3(children="Portfolio")),
                dbc.Col(
                    children=[
                        dcc.DatePickerRange(
                            id="portfolio_date",
                            start_date=start,
                            end_date=end,
                            with_portal=True,
                            min_date_allowed=start,
                            max_date_allowed=end,
                            start_date_placeholder_text="Select a Start Date",
                            end_date_placeholder_text="Select an End Date",
                            style={"body": {"background_color": "Black"}},
                        )
                    ],
                    align="center",
                    width=1.5,
                ),
            ],
            justify="between",
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[dcc.Graph(id="safety_first_ratio", figure=sfr_chart)],
                    width=1.5,
                ),
                dbc.Col(children=[dcc.Graph(id="value_at_risk", figure=var_chart)]),
            ],
            className="g-0",
        ),
    ]
)
