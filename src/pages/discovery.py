import dash
from dash import html, dcc, callback, Input, Output, dash_table, DiskcacheManager
from dash.dash_table import DataTable, FormatTemplate
import diskcache

cache = diskcache.Cache("../cache")
background_callback_manager = DiskcacheManager(cache)

import dash_bootstrap_components as dbc
from src.data import yahoo
from src.analysis import ticker_regression
from datetime import datetime as dt
import pandas as pd

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

dash.register_page(__name__, order=4)

money = FormatTemplate.money(2)
percentage = FormatTemplate.percentage(0)

growth_df = yahoo.retrieve_stocks_by_growth()
pred_df = ticker_regression.retrieve_model_results_from_mongo()
last_refresh = growth_df["Date"][0].strftime("%Y-%m-%d")
# analyst_df = yahoo.retrieve_stocks_by_analyst()
growth_df_top_5 = growth_df[["ticker", "Close", "close_pct_1yr"]].head()
growth_df_bottom_5 = growth_df[["ticker", "Close", "close_pct_1yr"]].tail().iloc[::-1]
growth_df_bottom_5.sort_values(['close_pct_1yr'], ascending=True, inplace=True)

sectors = growth_df["sector"].unique()
industries = list(growth_df["industry"].unique())
tickers = list(growth_df["ticker"].unique())
close = list(growth_df['Close'])
close.sort()
close_high = close[len(close) - 1]
close_low = close[0]
sectors.sort()
industries.sort()
sector_colors = dict(zip(sectors, px.colors.qualitative.Plotly))
industry_colors = dict(zip(industries, px.colors.qualitative.Plotly))
tickers.sort()

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
}

SLIDER_STYLE = {
    "color": "white",
    "font-size": "10px",
    "margin": "5px",
}

growth_by_sector_scatter = html.Div(
    [html.H4("Past Growth by Stock"), html.P("Displays the growth percentage since one year ago.  Stocks with a negative growth percentage since last year may be good investments this year depending on their predicted growth."), dcc.Graph(id="growth-scatter-plot")]
)

sector_box_plot = html.Div(
    [html.H4("Past Growth Variance"), html.P("Helps explain the growth percentages variance since one year ago for each sector/industry, displaying their overall trends"), dcc.Graph(id="sector-box-plot")]
)

analyst_recommendations_scatter = html.Div(
    [html.H4("Future Growth - Analyst Predicted"), html.P("Displays the predicted one year growth of a stock by analysts.  Stocks with a positive analyst growth and predicted growth may be good investments"), dcc.Graph(id="analyst-scatter-plot")]
)

model_visualization = html.Div(
    [html.H4("Future Growth - Model Predicted"), html.P("Displays the predicted one year growth of a stock through a trained Random Forest model.  Stocks with a positive predicted growth and analyst growth may be good investments"), dcc.Graph(id="model-scatter-plot")]
)

top_growth_stocks = html.Div(
    [
        html.H4("Top Performing Stocks"),
        dash_table.DataTable(
            id="growth_top_table",
            columns=[
                dict(id="ticker", name="Ticker"),
                dict(
                    id="Close",
                    name="Current Price",
                    type="numeric",
                    format=money,
                ),
                dict(
                    id="close_pct_1yr",
                    name="1yr Growth",
                    type="numeric",
                    format=percentage,
                ),
            ],
            data=growth_df_top_5.to_dict("records"),
            style_cell=dict(textAlign="right", font_family='sans-serif', padding="3px", border="none"),
            style_header=dict(backgroundColor="#005999", font_family='sans-serif', color="white", size=16, border="none"),
            style_data=dict(backgroundColor="#060606", font_family='sans-serif', color="white", border="none"),
        ),
    ]
)

worst_growth_stocks = html.Div(
    [
        html.H4("Worst Performing Stocks"),
        dash_table.DataTable(
            id="growth_bottom_table",
            columns=[
                dict(id="ticker", name="Ticker"),
                dict(
                    id="Close",
                    name="Current Price",
                    type="numeric",
                    format=money,
                ),
                dict(
                    id="close_pct_1yr",
                    name="1yr Decline",
                    type="numeric",
                    format=percentage,
                ),
            ],
            data=growth_df_bottom_5.to_dict("records"),
            style_as_list_view=True,
            style_cell=dict(textAlign="right", font_family='sans-serif', padding="3px", border="none"),
            style_header=dict(backgroundColor="#005999", font_family='sans-serif', color="white", size=16, border="none"),
            style_data=dict(backgroundColor="#060606", font_family='sans-serif', color="white", border="none"),
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
                                dbc.Col(
                                    html.P("Last Refresh: " + str(last_refresh), style={"text-align": "right", "font-size": "16px"}),
                                    width={"size": 6},
                                ),
                            ]
                        )
                    ],
                    style=FILTER_STYLE,
                    width={"size": 12},
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(sector_box_plot, width={"size": 6}),
                dbc.Col(analyst_recommendations_scatter, width={"size": 6}),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(dbc.Col(growth_by_sector_scatter, width={"size": 12})),
                        dbc.Row(
                            [
                                dbc.Col(top_growth_stocks, width={"size": 6}),
                                dbc.Col(worst_growth_stocks, width={"size": 6}),
                            ]
                        ),
                    ],
                    width={"size": 6},
                ),
                dbc.Col(model_visualization, width={"size": 6}),
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
    background=True,
    manager=background_callback_manager,
)
def update_ticker_dropdown(sector_options, industry_options):
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
    df = growth_df.copy()
    chart_sector=True
    fig = None
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
        if len(sector_options) == 1:
            chart_sector=False
        else:
            chart_sector=True
    if industry_options is not None and len(industry_options) >= 1:
        chart_sector=False
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        chart_sector=True
        df = df[df["ticker"].isin(ticker_options)]
    df["close_pct_1yr"] = df["close_pct_1yr"].astype(float)
    df["Close"] = df["Close"].astype(float)
    if chart_sector:
        df.sort_values(['sector'], ascending=True, inplace=True)
        fig = px.scatter(
            df,
            x="Close",
            y="close_pct_1yr",
            color="sector",
            color_discrete_map=sector_colors,
            hover_data=["ticker", "Close", "close_pct_1yr"],
            labels={
                        "Close": "Current Price",
                        "close_pct_1yr": "Past 1yr Growth",
                        "sector": "Sector",
                        "industry": "Industry",
                        "ticker": "Ticker",
                    },
        )
    else:
        df.sort_values(['industry'], ascending=True, inplace=True)
        fig = px.scatter(
            df,
            x="Close",
            y="close_pct_1yr",
            color="industry",
            color_discrete_map=industry_colors,
            hover_data=["ticker", "Close", "close_pct_1yr"],
            labels={
                        "Close": "Current Price",
                        "close_pct_1yr": "Past 1yr Growth",
                        "sector": "Sector",
                        "industry": "Industry",
                        "ticker": "Ticker",
                    },
        )
    fig.update_layout(
        dict(plot_bgcolor="#060606", paper_bgcolor="#060606", font_color="white", xaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False, tickprefix = '$'), yaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False, tickformat=",.0%"))
    )
    return fig

@callback(
    Output("sector-box-plot", "figure"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
)
def update_sector_box_plot(sector_options, industry_options, ticker_options):
    df = growth_df.copy()
    df["close_pct_1yr"] = df["close_pct_1yr"].astype(float)
    df = df.sort_values(by=["sector", "industry", "ticker"])
    df["sector"] = df["sector"].fillna("Other Sector")
    df["industry"] = df["industry"].fillna("Other Industry")
    chart_sector = True
    fig = None
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
        if len(sector_options) == 1:
            chart_sector=False
        else:
            chart_sector=True
    if industry_options is not None and len(industry_options) >= 1:
        chart_sector=False
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        chart_sector=True
        df = df[df["ticker"].isin(ticker_options)]
    if chart_sector:
        df.sort_values(['sector'], ascending=True, inplace=True)
        fig = px.box(df, x="sector", y="close_pct_1yr", color="sector", color_discrete_map=sector_colors, points="outliers",
                labels={
                                "sector": "Sector", 
                                "industry": "Industry", 
                                "ticker": "Ticker",
                                "close_pct_1yr": "Past 1yr Growth",
                            },)
    else:
        df.sort_values(['industry'], ascending=True, inplace=True)
        fig = px.box(df, x="industry", y="close_pct_1yr", color="industry", color_discrete_map=industry_colors, points="outliers",
            labels={
                            "sector": "Sector", 
                            "industry": "Industry", 
                            "ticker": "Ticker",
                            "close_pct_1yr": "Past 1yr Growth",
                        },)
    fig.update_layout(plot_bgcolor="#060606", paper_bgcolor="#060606", font_color="white", showlegend=False, xaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False), yaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False, tickformat=",.0%"))
    return fig


@callback(
    Output("analyst-scatter-plot", "figure"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),    
)
def update_analyst_scatter_chart(sector_options, industry_options, ticker_options):
    analyst_df = yahoo.retrieve_stocks_by_analyst()
    df = analyst_df.copy()
    chart_sector = True
    fig = None
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
        if len(sector_options) == 1:
            chart_sector=False
        else:
            chart_sector=True
    if industry_options is not None and len(industry_options) >= 1:
        chart_sector=False
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        chart_sector=True
        df = df[df["ticker"].isin(ticker_options)]
    df["targetMedianPrice"] = df["targetMedianPrice"].astype(float)
    df["targetMedianGrowth"] = df["targetMedianGrowth"].astype(float)
    df["numberOfAnalystOpinions"] = df["numberOfAnalystOpinions"].astype(int)
    if chart_sector:
        df.sort_values(['sector'], ascending=True, inplace=True)
        fig = px.scatter(
            df,
            x="numberOfAnalystOpinions",
            y="targetMedianGrowth",
            color="sector",
            color_discrete_map=sector_colors,
            hover_data={"ticker":True , "Close": ":$,.2f", "targetMedianGrowth":True, "targetMedianPrice": ":$,.2f", "numberOfAnalystOpinions":True},
            labels={
                        "numberOfAnalystOpinions": "Number of Analyst Opinions",
                        "targetMedianGrowth": "Target Median 1yr Growth",
                        "targetMedianPrice": "Target Median 1yr Price",
                        "sector": "Sector", 
                        "industry": "Industry", 
                        "ticker": "Ticker",
                        "Close": "Current Price",
                    },
        )
    else:
        df.sort_values(['industry'], ascending=True, inplace=True)
        fig = px.scatter(
            df,
            x="numberOfAnalystOpinions",
            y="targetMedianGrowth",
            color="industry",
            color_discrete_map=industry_colors,
            hover_data={"ticker":True , "Close": ":$,.2f", "targetMedianGrowth":True, "targetMedianPrice": ":$,.2f", "numberOfAnalystOpinions":True},
            labels={
                        "numberOfAnalystOpinions": "Number of Analyst Opinions",
                        "targetMedianGrowth": "Target Median 1yr Growth",
                        "targetMedianPrice": "Target Median 1yr Price",
                        "sector": "Sector", 
                        "industry": "Industry", 
                        "ticker": "Ticker",
                        "Close": "Current Price",
                    },
        )
    fig.update_layout(
        dict(plot_bgcolor="#060606", paper_bgcolor="#060606", font_color="white", xaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False), yaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False, tickformat=",.0%"))
    )
    return fig

@callback(
    Output("model-scatter-plot", "figure"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
    background=True,
    manager=background_callback_manager,
)
def update_model_chart(sector_options, industry_options, ticker_options):
    df = pred_df.copy()
    chart_sector=True
    fig = None
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
        if len(sector_options) == 1:
            chart_sector=False
        else:
            chart_sector=True
    if industry_options is not None and len(industry_options) >= 1:
        chart_sector=False
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        chart_sector=True
        df = df[df["ticker"].isin(ticker_options)]
    df["predicted_1yr_growth"] = df["predicted_1yr_growth"].astype(float)
    df["Close"] = df["Close"].astype(float)
    if chart_sector:
        df.sort_values(['sector'], ascending=True, inplace=True)
        fig = px.scatter(
            df,
            x="prediction",
            y="predicted_1yr_growth",
            color="sector",
            color_discrete_map=sector_colors,
            hover_data=["ticker", "Date", "predicted_1yr_growth", "prediction", "train_score", "test_score"],
            labels={
                        "Date": "Date",
                        "predicted_1yr_growth": "Predicted 1yr Growth",
                        "prediction": "Predicted 1yr Price",
                        "sector": "Sector",
                        "industry": "Industry",
                        "ticker": "Ticker",
                        "train_score": "Train Score",
                        "test_score": "Test Score"
                    },
        )
    else:
        df.sort_values(['industry'], ascending=True, inplace=True)
        fig = px.scatter(
            df,
            x="prediction",
            y="predicted_1yr_growth",
            color="industry",
            color_discrete_map=industry_colors,
            hover_data=["ticker", "Date", "predicted_1yr_growth", "prediction", "train_score", "test_score"],
            labels={
                        "Date": "Date",
                        "predicted_1yr_growth": "Predicted 1yr Growth",
                        "prediction": "Predicted 1yr Price",
                        "sector": "Sector",
                        "industry": "Industry",
                        "ticker": "Ticker",
                        "train_score": "Train Score",
                        "test_score": "Test Score"
                    },
        )
    fig.update_layout(
        dict(plot_bgcolor="#060606", paper_bgcolor="#060606", font_color="white", xaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False, tickprefix = '$'), yaxis=dict(zerolinecolor="white", zerolinewidth = 1, showgrid=False, tickformat=",.0%"))
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
    df = growth_df.copy()
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
    if industry_options is not None and len(industry_options) >= 1:
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        df = df[df["ticker"].isin(ticker_options)]
    df = df[["ticker", "Close", "close_pct_1yr"]].head()
    data = df.to_dict("records")
    return data


@callback(
    Output("growth_bottom_table", "data"),
    Input("sector-dropdown", "value"),
    Input("industry-dropdown", "value"),
    Input("ticker-dropdown", "value"),
    background=True,
    manager=background_callback_manager,
)
def update_growth_bottom_table(sector_options, industry_options, ticker_options):
    df = growth_df.copy()
    if sector_options is not None and len(sector_options) >= 1:
        df = df[df["sector"].isin(sector_options)]
    if industry_options is not None and len(industry_options) >= 1:
        df = df[df["industry"].isin(industry_options)]
    if ticker_options is not None and len(ticker_options) >= 1:
        df = df[df["ticker"].isin(ticker_options)]
    df = df[["ticker", "Close", "close_pct_1yr"]].tail()
    df.sort_values(['close_pct_1yr'], ascending=True, inplace=True)
    data = df.to_dict("records")
    return data