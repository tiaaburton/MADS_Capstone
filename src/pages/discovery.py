import dash
from dash import html, dcc, callback, Input, Output, dash_table, DiskcacheManager
from dash.dash_table import DataTable, FormatTemplate
import diskcache
cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

import dash_bootstrap_components as dbc
from src.utils import generate_line_graph
from src.data import yahoo

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

dash.register_page(__name__, order=4)

money = FormatTemplate.money(2)
percentage = FormatTemplate.percentage(0)

growth_df = yahoo.retrieve_stocks_by_growth()
# analyst_df = yahoo.retrieve_stocks_by_analyst()
growth_df_top_5 = growth_df[["ticker", "close_pct_1yr"]].head()
growth_df_bottom_5 = growth_df[["ticker", "close_pct_1yr"]].tail().iloc[::-1]

sectors = growth_df["sector"].unique()
industries = list(growth_df["industry"].unique())
tickers = list(growth_df["ticker"].unique())
sectors.sort()
industries.sort()
tickers.sort()

# growth_df.style.format({'close_pct_1yr': '{:,.0%}'.format})

# top_growth_stocks = go.Figure(data=[go.Table(header=dict(values=['Ticker', '1 Yr Growth'], fill_color='#119DFF', line_color='white', align='center', font=dict(color='white', size=16)),
#                  cells=dict(values=[growth_df['ticker'][:5], growth_df['close_pct_1yr'][:5]], fill_color='black', line_color='white', align='right', font=dict(color='white', size=16)))
#                      ])

FILTER_STYLE = {
    # "position": "fixed",
    # "top": 0,
    # "left": 0,
    # "width": "22rem",
    "background-color": "#005999",
    # "padding": "2rem 1rem",
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
}

filters = html.Div(
    [
        html.Div(dcc.Dropdown(sectors, id="sector-dropdown")),
        html.Div(dcc.Dropdown(industries, id="industry-dropdown")),
        html.Div(dcc.Dropdown(tickers, id="ticker-dropdown")),
    ],
    style=FILTER_STYLE,
)

growth_by_sector_scatter = html.Div(
    [html.H4("Yearly Growth by Stock"), dcc.Graph(id="growth-scatter-plot")]
)

growth_by_sector_icicle = html.Div(
    [html.H4("Yearly Growth by Sector"), dcc.Graph(id="growth-icicle-chart")]
)

analyst_recommendations_scatter = html.Div(
    [html.H4("Analyst Recommendations"), dcc.Graph(id="analyst-scatter-plot")]
)

top_growth_stocks = html.Div(
    [
        html.H4("Top Performing Stocks"),
        dash_table.DataTable(
            id="growth_top_table",
            # columns=[{"name": i, "id": i}
            #         for i in growth_df_top_5.columns],
            columns=[
                dict(id="ticker", name="Ticker"),
                dict(
                    id="close_pct_1yr",
                    name="1yr Growth",
                    type="numeric",
                    format=percentage,
                ),
            ],
            data=growth_df_top_5.to_dict("records"),
            style_cell=dict(textAlign="left", padding="3px"),
            style_header=dict(backgroundColor="#005999", color="white", size=16),
            style_data=dict(backgroundColor="#e6e6e6", color="black"),
        ),
    ]
)

worst_growth_stocks = html.Div(
    [
        html.H4("Worst Performing Stocks"),
        dash_table.DataTable(
            id="growth_bottom_table",
            # columns=[{"name": i, "id": i}
            #         for i in growth_df_top_5.columns],
            columns=[
                dict(id="ticker", name="Ticker"),
                dict(
                    id="close_pct_1yr",
                    name="1yr Growth",
                    type="numeric",
                    format=percentage,
                ),
            ],
            data=growth_df_bottom_5.to_dict("records"),
            style_as_list_view=True,
            style_cell=dict(textAlign="left", padding="3px"),
            style_header=dict(backgroundColor="#005999", color="white", size=16),
            style_data=dict(backgroundColor="#e6e6e6", color="black"),
        ),
    ]
)

layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        dcc.Dropdown(
                                            sectors,
                                            id="sector-dropdown",
                                            placeholder="Select a sector",
                                            multi=True,
                                        ),
                                        style=DROPDOWN_STYLE,
                                    ),
                                    width={"size": 2},
                                ),
                                dbc.Col(
                                    html.Div(
                                        dcc.Dropdown(
                                            industries,
                                            id="industry-dropdown",
                                            placeholder="Select an industry",
                                            multi=True,
                                        ),
                                        style=DROPDOWN_STYLE,
                                    ),
                                    width={"size": 2},
                                ),
                                dbc.Col(
                                    html.Div(
                                        dcc.Dropdown(
                                            tickers,
                                            id="ticker-dropdown",
                                            placeholder="Select a ticker",
                                            multi=True,
                                        ),
                                        style=DROPDOWN_STYLE,
                                    ),
                                    width={"size": 2},
                                ),
                            ]
                        )
                    ],
                    style=FILTER_STYLE,
                    width={"size": 12},
                )
                # dbc.Col(html.Div(children=[filters]), style=FILTER_STYLE)
                # dbc.Col(html.Div("Stock Performance by Sector"), style=FILTER_STYLE)
                # dbc.Col(html.Div(dcc.Dropdown(['Utilities', 'Other'], id='sector-dropdown')), style=FILTER_STYLE)
            ]
        ),
        dbc.Row(
            [
                dbc.Col(growth_by_sector_icicle, width={"size": 6}),
                dbc.Col(analyst_recommendations_scatter, width={"size": 6}),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(dbc.Col(growth_by_sector_scatter, width={"size": 12})),
                        # dbc.Row(dbc.Col(html.Div("Stock Sector Scatter"), width={"size": 12})),
                        dbc.Row(
                            [
                                dbc.Col(top_growth_stocks, width={"size": 6}),
                                dbc.Col(worst_growth_stocks, width={"size": 6}),
                            ]
                        ),
                    ],
                    width={"size": 6},
                ),
                dbc.Col(html.Div("Model Visualization"), width={"size": 6}),
            ]
        ),
    ]
)


@callback(
    Output("industry-dropdown", "options"),
    Input("sector-dropdown", "value"),
    background=True,
    manager=background_callback_manager,
)
def update_industry_dropdown(sector_options):
    # growth_df = yahoo.retrieve_stocks_by_growth()
    # industries = list(growth_df["industry"].unique())
    # industries.sort()
    if sector_options is None or sector_options == []:
        return industries
    new_industries = growth_df[growth_df["sector"].isin(sector_options)][
        "industry"
    ].unique()
    new_industries.sort()
    return new_industries


@callback(
    Output("ticker-dropdown", "options"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
)
def update_ticker_dropdown(sector_options, industry_options):
    # growth_df = yahoo.retrieve_stocks_by_growth()
    # tickers = list(growth_df["ticker"].unique())
    # tickers.sort()
    new_tickers = []
    if (sector_options == [] or sector_options == None) and (
        industry_options == [] or industry_options == None
    ):
        return tickers
    elif len(sector_options) >= 1 and (
        industry_options == [] or industry_options == None
    ):
        new_tickers = growth_df[growth_df["sector"].isin(sector_options)][
            "ticker"
        ].unique()
    elif (sector_options == [] or sector_options == None) and len(
        industry_options
    ) >= 1:
        new_tickers = growth_df[growth_df["industry"].isin(industry_options)][
            "ticker"
        ].unique()
    else:
        new_tickers = growth_df[
            (growth_df["sector"].isin(sector_options))
            & (growth_df["industry"].isin(industry_options))
        ]["ticker"].unique()
    new_tickers.sort()
    return new_tickers


@callback(
    Output("growth-scatter-plot", "figure"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
    background=True,
    manager=background_callback_manager,
)
def update_scatter_chart(sector_options, industry_options, ticker_options):
    # growth_df = yahoo.retrieve_stocks_by_growth()
    df = growth_df.copy()
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
    if industry_options is not None and len(industry_options) >= 1:
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        df = df[df["ticker"].isin(ticker_options)]
    df["close_pct_1yr"] = df["close_pct_1yr"].astype(float)
    df["Close"] = df["Close"].astype(float)
    fig = px.scatter(
        df,
        x="Close",
        y="close_pct_1yr",
        color="sector",
        hover_data=["ticker", "Close", "close_pct_1yr"],
    )
    fig.update_layout(
        dict(plot_bgcolor="#e6e6e6", paper_bgcolor="#e6e6e6", font_color="black")
    )
    return fig


@callback(
    Output("growth-icicle-chart", "figure"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
    background=True,
    manager=background_callback_manager,
)
def update_icicle_chart(sector_options, industry_options, ticker_options):
    # growth_df = yahoo.retrieve_stocks_by_growth()
    df = growth_df.copy()
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
    if industry_options is not None and len(industry_options) >= 1:
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        df = df[df["ticker"].isin(ticker_options)]
    df["close_pct_1yr"] = df["close_pct_1yr"].astype(float)
    df["all"] = "all"  # in order to have a single root node
    df = df.sort_values(by=["sector", "industry", "ticker"])
    df["sector"] = df["sector"].fillna("Other Sector")
    df["industry"] = df["industry"].fillna("Other Industry")
    fig = px.icicle(
        df, path=["all", "sector", "industry", "ticker"], values="close_pct_1yr"
    )
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    return fig


@callback(
    Output("analyst-scatter-plot", "figure"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
    background=True,
    manager=background_callback_manager,
)
def update_analyst_scatter_chart(sector_options, industry_options, ticker_options):
    analyst_df = yahoo.retrieve_stocks_by_analyst()
    df = analyst_df.copy()
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
    if industry_options is not None and len(industry_options) >= 1:
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        df = df[df["ticker"].isin(ticker_options)]
    df["targetMedianPrice"] = df["targetMedianPrice"].astype(float)
    df["numberOfAnalystOpinions"] = df["numberOfAnalystOpinions"].astype(int)
    fig = px.scatter(
        df,
        x="numberOfAnalystOpinions",
        y="targetMedianPrice",
        color="sector",
        hover_data=["ticker", "Close", "targetMedianPrice", "numberOfAnalystOpinions"],
    )
    fig.update_layout(
        dict(plot_bgcolor="#e6e6e6", paper_bgcolor="#e6e6e6", font_color="black")
    )
    return fig


@callback(
    Output("growth_top_table", "data"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
    background=True,
    manager=background_callback_manager,
)
def update_growth_top_table(sector_options, industry_options, ticker_options):
    # growth_df = yahoo.retrieve_stocks_by_growth()
    df = growth_df.copy()
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
    if industry_options is not None and len(industry_options) >= 1:
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        df = df[df["ticker"].isin(ticker_options)]
    df = df[["ticker", "close_pct_1yr"]].head()
    data = df.to_dict("records")
    return data


@callback(
    Output("growth_bottom_table", "data"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
)
def update_growth_bottom_table(sector_options, industry_options, ticker_options):
    # growth_df = yahoo.retrieve_stocks_by_growth()
    df = growth_df.copy()
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
    if industry_options is not None and len(industry_options) >= 1:
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        df = df[df["ticker"].isin(ticker_options)]
    df = df[["ticker", "close_pct_1yr"]].tail()
    data = df.to_dict("records")
    return data


# @callback(
#     Output('growth_top_table_out', 'children'),
#     Input('growth_top_table', 'active_cell'))
# def update_graphs(active_cell):
#     if active_cell:
#         cell_data = growth_df_top_5.iloc[active_cell['row']][active_cell['column_id']]
#         return f"Data: \"{cell_data}\" from table cell: {active_cell}"
#     return "Click the table"

# @callback(
#     Output('growth_bottom_table_out', 'children'),
#     Input('growth_bottom_table', 'active_cell'))
# def update_graphs(active_cell):
#     if active_cell:
#         cell_data = growth_df_bottom_5.iloc[active_cell['row']][active_cell['column_id']]
#         return f"Data: \"{cell_data}\" from table cell: {active_cell}"
#     return "Click the table"


# stock_sector_scatter = html.Div(
#     [
#         dcc.Graph(id="indices_chart"),
#         dcc.Slider(
#             df["Close"].min(),
#             df["Close"].max(),
#             step=None,
#             value=df["Close"].min(),
#             marks={str(year): str(year) for year in df["Date"].unique()},
#             id="close-slider",
#         ),
#     ]
# )
