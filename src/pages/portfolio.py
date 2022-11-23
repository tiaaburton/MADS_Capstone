from pathlib import Path

import dash
import diskcache
from dash import html, dcc, callback, Input, Output, DiskcacheManager
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

from src.analysis.portfolio_stats import portfolioCharts

cache = diskcache.Cache("../cache")
background_callback_manager = DiskcacheManager(cache)

p_str = f"{str(Path(__file__).parents[1])}/test_portfolio.csv"
start = dt.datetime(2022, 9, 1).date()
end = dt.datetime.today().date()
p = test_portfolio(p_str)

portfolio_charts = portfolioCharts()

dash.register_page(__name__, order=2)

layout = html.Div(
    children=[
        dbc.Row(
            children=[
                dbc.Col(html.H3(children="Portfolio"), width=2),
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
                    width=4,
                ),
                dbc.Col(
                    html.Div("Select expected returns:"),
                    width=2,
                    align="center",
                ),
                dbc.Col(
                    dcc.Slider(
                        0,
                        100,
                        1,
                        value=2,
                        marks=None,
                        id="expected_returns",
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    align="center",
                ),
            ],
            justify="between",
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[dcc.Graph(id="safety_first_ratio")],
                    width=3,
                ),
                dbc.Col(children=[dcc.Graph(id="value_at_risk")]),
            ],
            className="g-0",
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    dcc.Graph(
                        id="sector_chart", figure=portfolio_charts.create_sector_chart()
                    )
                ),
                dbc.Col(
                    dcc.Graph(
                        id="worth_chart", figure=portfolio_charts.create_worth_chart()
                    )
                ),
            ]
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    dcc.Graph(
                        id="changes_chart",
                        figure=portfolio_charts.create_changes_chart(),
                    )
                ),
                dbc.Col(
                    dcc.Graph(
                        id="worth_table", figure=portfolio_charts.create_worth_table()
                    )
                ),
            ]
        ),
    ]
)


@callback(
    Output(component_id="safety_first_ratio", component_property="figure"),
    Input(component_id="expected_returns", component_property="value"),
    Input(component_id="portfolio_date", component_property="start_date"),
    Input(component_id="portfolio_date", component_property="end_date"),
    background=True,
    manager=background_callback_manager,
)
def update_sfr(expected_returns, start_date, end_date):
    sfr = calculate_SFR(
        p, exp_return=(expected_returns / 100), start_date=start_date, end_date=end_date
    )
    return SFR_Chart(sfr).create_chart()


@callback(
    Output(component_id="value_at_risk", component_property="figure"),
    Input(component_id="portfolio_date", component_property="start_date"),
    Input(component_id="portfolio_date", component_property="end_date"),
    background=True,
    manager=background_callback_manager,
)
def update_var(start_date, end_date):
    var = calculate_VaR(
        start_date=start_date,
        end_date=end_date,
        portfolio=p,
    )
    return VaR_Chart(var).create_chart()
