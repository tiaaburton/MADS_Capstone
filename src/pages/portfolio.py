import dash
import datetime as dt
import dash_bootstrap_components as dbc

from src.analysis.safety_measures import (
    create_portfolio_df,
    VaR_Chart,
    calculate_SFR,
    calculate_VaR,
)
from dash import html, dcc, callback, Input, Output
from src.analysis.portfolio_stats import portfolioCharts
from src.analysis.t_tests import get_available_portfolios

start = dt.datetime(2022, 9, 1).date()
end = dt.datetime.today().date()

portfolios = get_available_portfolios()

FILTER_STYLE = {
    "background-color": "#005999",
    "color": "white",
    "font-size": "14px",
    "text-align": "right",
    "right": 0,
}

DROPDOWN_STYLE = {
    "background-color": "#005999",
    "color": "black",
    "font-size": "12px",
    "margin": "5px",
    "text-align": "left",
}

dash.register_page(__name__, order=2)

layout = html.Div(
    children=[
        dbc.Row(
            children=[
                dbc.Col(
                    html.Div("Select expected returns :"),
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
                    width=4,
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="portfolio",
                        options=[
                            {
                                "label": value.split("/")[-1][:-4]
                                .replace("_", " ")
                                .capitalize(),
                                "value": value,
                            }
                            for value in portfolios
                        ],
                        value=portfolios[0],
                        style=DROPDOWN_STYLE,
                    ),
                    width=3,
                ),
                dbc.Col(
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
                    ),
                ),
            ],
            justify="between",
            style=FILTER_STYLE,
            className="g-0",
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[html.P(id="safety_first_ratio")],
                    align="center",
                    width={"width": 3, "offset": 1},
                )
            ]
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dcc.Graph(
                            id="changes_chart",
                        )
                    ]
                ),
                dbc.Col(children=[dcc.Graph(id="value_at_risk")]),
            ],
            className="g-0",
            justify="center",
        ),
        dbc.Row(
            children=[
                dbc.Col(dcc.Graph(id="worth_table")),
                dbc.Col(
                    children=[
                        dcc.Dropdown(
                            options=["By Sector", "By Sector and Stock"],
                            value="By Sector",
                            id="portfolio_worth",
                        ),
                        dcc.Graph(id="worth_chart"),
                    ]
                ),
            ]
        ),
    ]
)


@callback(
    # Output(component_id="safety_first_ratio", component_property="figure"),
    Output(component_id="safety_first_ratio", component_property="children"),
    Input(component_id="expected_returns", component_property="value"),
    Input(component_id="portfolio_date", component_property="start_date"),
    Input(component_id="portfolio_date", component_property="end_date"),
    Input(component_id="portfolio", component_property="value"),
    background=True,
)
def update_sfr(expected_returns, start_date, end_date, portfolio):
    """Creates a dynamic Safety First Ratio chart based on a user's selections.

    :param expected_returns: Corresponds with the expected returns slider. Initial value set at 2,
    which represents 2% expected returns.
    :param start_date: The first day of data in which the ratio will be based upon.
    :param end_date: The last day of data in which the ratio will be based upon.
    :param portfolio: Full path string representing the selected truncated file path. File must be in
    the format specified in the README.md file.
    :return safety_first_ratio: Plotly chart is returned as a figure to be added to the layout."""

    sfr = calculate_SFR(
        create_portfolio_df(portfolio),
        exp_return=(expected_returns / 100),
        start_date=start_date,
        end_date=end_date,
    )
    if sfr >= 0:
        portfolio_opt = "This portfolio is fit for your expected returns, but there may be enhancements to continue to increase you returns."
    else:
        portfolio_opt = "This portfolio is not likely to meet your desired returns. It is suggested to optimize your portfolio and try again."
    # SFR_Chart(sfr).create_chart()
    port_name = portfolio.split("/")[-1].replace("_", " ").capitalize()
    return (
        f"""Safety First Ratio for {port_name[:-4]}: {round(sfr, 2)}. {portfolio_opt}"""
    )


@callback(
    Output(component_id="value_at_risk", component_property="figure"),
    Input(component_id="portfolio_date", component_property="start_date"),
    Input(component_id="portfolio_date", component_property="end_date"),
    Input(component_id="portfolio", component_property="value"),
    background=True,
)
def update_var(start_date, end_date, portfolio):
    """Creates a dynamic Value at Risk chart based on a user's selections.

    :param start_date: The first day of data in which the ratio will be based upon.
    :param end_date: The last day of data in which the ratio will be based upon.
    :param portfolio: Full path string representing the selected truncated file path. File must be in
    the format specified in the README.md file.
    :return value_at_risk: Plotly chart is returned as a figure to be added to the layout."""

    var = calculate_VaR(
        start_date=start_date,
        end_date=end_date,
        portfolio=create_portfolio_df(portfolio),
    )
    return VaR_Chart(var).create_chart()


@callback(
    Output(component_id="worth_chart", component_property="figure"),
    Output(component_id="worth_table", component_property="figure"),
    Output(component_id="changes_chart", component_property="figure"),
    Input(component_id="portfolio", component_property="value"),
    Input(component_id="portfolio_worth", component_property="value"),
    background=True,
)
def change_worth_chart_type(file_loc, chart_type):
    portfolio_charts = portfolioCharts().update_portfolio(new_portfolio=file_loc)
    if chart_type == "By Sector":
        return (
            portfolio_charts.create_sector_chart(),
            portfolio_charts.create_worth_table(),
            portfolio_charts.create_changes_chart(),
        )
    elif chart_type == "By Sector and Stock":
        return (
            portfolio_charts.create_worth_chart(),
            portfolio_charts.create_worth_table(),
            portfolio_charts.create_changes_chart(),
        )
