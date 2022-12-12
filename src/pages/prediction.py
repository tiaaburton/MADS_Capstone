import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta

# Dashboard-related libraries
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc


# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# MASS Packages
import pandas as pd
from datetime import date
from datetime import timedelta
import matplotlib.pyplot as plt
import yahoo_fin.stock_info as si
from pytictoc import TicToc
import numpy as np
import numpy.testing as npt
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

t = TicToc()
import stumpy
from dateutil import parser

dash.register_page(__name__, order=5)

TABS_STYLES = {"height": "44px"}

TAB_STYLE = {
    "borderBottom": "1px solid #d6d6d6",
    "padding": "6px",
    "fontWeight": "bold",
    "backgroundColor": "#787878",
}

TAB_SELECTED_STYLE = {
    "borderTop": "1px solid #d6d6d6",
    "borderBottom": "1px solid #d6d6d6",
    "backgroundColor": "#119DFF",
    "color": "white",
    "padding": "6px",
}

FILTER_STYLE = {
    "background-color": "#005999",
    "color": "white",
    "font-size": "14px",
    "text-align": "right",
    "right": 0,
}

pd.set_option("mode.chained_assignment", None)


def generate_line_graph(df, x, y, title):

    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig = fig.add_trace(go.Scatter(x=df[x], y=df[y], name=y))
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center"),
        template="plotly_dark",
        showlegend=True,
        margin=dict(b=20, t=50, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(connectgaps=True)
    fig.update_xaxes(showgrid=False),
    fig.update_yaxes(showgrid=False),

    return fig


graph_df = pd.read_csv("https://nacey-capstone.s3.amazonaws.com/model_data_1d.csv")
dl_df = pd.read_csv("https://nacey-capstone.s3.amazonaws.com/keras_preds.csv")
xgb_df = pd.read_csv("https://nacey-capstone.s3.amazonaws.com/xgboost_preds.csv")
cs_df = pd.read_csv("https://nacey-capstone.s3.amazonaws.com/cs_preds.csv")

graph_df = graph_df.rename(columns={"SPX_x": "SPX"})


periods = [1, 5, 10, 15, 20, 40, 60, 120]

# Construct DL Prediction chart
dl_df = dl_df.drop("Unnamed: 0", axis=1)
dl_level_df = (dl_df + 1) * graph_df["SPX"].tail(1).item()
last_day = pd.to_datetime(graph_df.tail(1)["Date"]).item()
dl_level_df["Date"] = np.nan
date_list = []
for period in periods:
    date_list.append(last_day + timedelta(days=period))
dl_level_df["Date"] = date_list
dl_graph = generate_line_graph(graph_df.tail(200), "Date", "SPX", "")
dl_graph.add_trace(go.Scatter(x=dl_level_df["Date"], y=dl_level_df["1d"], name="1d"))
dl_graph.add_trace(go.Scatter(x=dl_level_df["Date"], y=dl_level_df["5d"], name="5d"))
dl_graph.add_trace(go.Scatter(x=dl_level_df["Date"], y=dl_level_df["SM"], name="SM"))
dl_graph.add_trace(go.Scatter(x=dl_level_df["Date"], y=dl_level_df["M"], name="M"))
dl_graph.add_trace(
    go.Scatter(x=dl_level_df["Date"], y=dl_level_df["Mean"], name="Mean")
)

# Construct XGBoost Prediction Chart
xgb_df = xgb_df.drop("Unnamed: 0", axis=1)
xgb_level_df = (xgb_df + 1) * graph_df["SPX"].tail(1).item()
last_day = pd.to_datetime(graph_df.tail(1)["Date"]).item()
xgb_level_df["Date"] = np.nan
date_list = []
for period in periods:
    date_list.append(last_day + timedelta(days=period))
xgb_level_df["Date"] = date_list
xgb_graph = generate_line_graph(graph_df.tail(200), "Date", "SPX", "")
xgb_graph.add_trace(go.Scatter(x=xgb_level_df["Date"], y=xgb_level_df["1d"], name="1d"))
xgb_graph.add_trace(go.Scatter(x=xgb_level_df["Date"], y=xgb_level_df["5d"], name="5d"))
xgb_graph.add_trace(go.Scatter(x=xgb_level_df["Date"], y=xgb_level_df["SM"], name="SM"))
xgb_graph.add_trace(go.Scatter(x=xgb_level_df["Date"], y=xgb_level_df["M"], name="M"))
xgb_graph.add_trace(
    go.Scatter(x=xgb_level_df["Date"], y=xgb_level_df["Mean"], name="Mean")
)

# Construct Cosine Similarity Prediction Chart
cs_df = cs_df.drop("Unnamed: 0", axis=1)
cs_level_df = (cs_df + 1) * graph_df["SPX"].tail(1).item()
last_day = pd.to_datetime(graph_df.tail(1)["Date"]).item()
cs_level_df["Date"] = np.nan
date_list = []
for period in periods:
    date_list.append(last_day + timedelta(days=period))
cs_level_df["Date"] = date_list
cs_graph = generate_line_graph(graph_df.tail(200), "Date", "SPX", "")
cs_graph.add_trace(go.Scatter(x=cs_level_df["Date"], y=cs_level_df["1d"], name="1d"))
cs_graph.add_trace(go.Scatter(x=cs_level_df["Date"], y=cs_level_df["5d"], name="5d"))
cs_graph.add_trace(go.Scatter(x=cs_level_df["Date"], y=cs_level_df["SM"], name="SM"))
cs_graph.add_trace(go.Scatter(x=cs_level_df["Date"], y=cs_level_df["M"], name="M"))
cs_graph.add_trace(
    go.Scatter(x=cs_level_df["Date"], y=cs_level_df["Mean"], name="Mean")
)


def serve_layout():
    layout = html.Div(
        children=[
            html.Br(),
            html.Div(
                children=[
                    # html.H4('S&P 500 Predictive Analytics'),
                    # html.Hr(),
                    html.Div(
                        children=[
                            dcc.Tabs(
                                children=[
                                    dcc.Tab(
                                        id="nn-ml-tab",
                                        label="Deep Learning Model",
                                        style=TAB_STYLE,
                                        selected_style=TAB_SELECTED_STYLE,
                                        children=[
                                            html.P(),
                                            html.Div(
                                                """Our deep learning model utilizes a multi-layer perceptron -- implemented via Keras -- that takes as input 
                                        various current market metrics such as price levels, technical indicators, economic indicators, 
                                        and custom signals.  These features are then resampled to different time periods in order to 
                                        determine if larger time windows can produce enhanced results.  This model is then used to predict
                                        future returns when given a vector of today's current market metrics.  Below you will find predictions
                                        given current data."""
                                            ),
                                            html.P(),
                                            html.Center(
                                                html.H4(
                                                    "S&P 500 Forward Trajectory - Deep Learning Model"
                                                )
                                            ),
                                            html.P(),
                                            dcc.Graph(figure=dl_graph),
                                        ],
                                    ),
                                    dcc.Tab(
                                        id="xgb-ml-tab",
                                        label="Boosted Tree Model",
                                        style=TAB_STYLE,
                                        selected_style=TAB_SELECTED_STYLE,
                                        children=[
                                            html.P(),
                                            html.Div(
                                                """Our machine learning model utilizes a gradient-boosted tree model -- implemented via XGBoost -- that takes 
                                        as input various current market metrics such as price levels, technical indicators, economic 
                                        indicators, and custom signals.  These features are then resampled to different time periods in order 
                                        to determine if larger time windows can produce enhanced results.  This model is then used to predict
                                        future returns when given a vector of today's current market metrics.  Below you will find predictions
                                        given current data."""
                                            ),
                                            html.P(),
                                            html.Center(
                                                html.H4(
                                                    "S&P 500 Forward Trajectory - Gradient-Boosted Tree Model"
                                                )
                                            ),
                                            html.P(),
                                            dcc.Graph(figure=xgb_graph),
                                        ],
                                    ),
                                    dcc.Tab(
                                        id="cs-ml-tab",
                                        label="Cosine Similarity",
                                        style=TAB_STYLE,
                                        selected_style=TAB_SELECTED_STYLE,
                                        children=[
                                            html.P(),
                                            html.Div(
                                                """Our cosine similarity model takes 
                                        as input various current market metrics such as price levels, technical indicators, economic 
                                        indicators, and custom signals.  These features are then resampled to different time periods in order 
                                        to determine if larger time windows can produce enhanced results.  We then measure the cosine
                                        similarity between a vector of today's data and all of the periods in our dataset.  This measure
                                        indicates which historical periods are most similar to current data.  We average the returns of the
                                        top 10 most similar periods to arrive at a prediction, as shown below."""
                                            ),
                                            html.P(),
                                            html.Center(
                                                html.H4(
                                                    "S&P 500 Forward Trajectory - Cosine Similarity Model"
                                                )
                                            ),
                                            html.P(),
                                            dcc.Graph(figure=cs_graph),
                                        ],
                                    ),
                                    dcc.Tab(
                                        id="mass-tab",
                                        label="MASS Pattern Matching",
                                        style=TAB_STYLE,
                                        selected_style=TAB_SELECTED_STYLE,
                                        children=[
                                            html.P(),
                                            html.Div(
                                                """In an attempt to identify analogous historical periods to today's market, we employ an algorithm below
                                        that matches the S&P 500 over a user specified window with a similar window in history.  This allows
                                        the user to not only see how the matched period progressed, but also to identify the dates of the
                                        matched period in order to investigate economic variables and market naratives at that time.  The
                                        method employed is Mueen's Algorithm for Similarity Search (MASS).  This method allows us to find
                                        matching patterns by minimizing the distance between each time series, however, it uses an efficient
                                        search algorithm to dramtically increase speed of compute."""
                                            ),
                                            html.P(),
                                            html.Div(
                                                """Below, please select a date that represents the start of the recent market window.  The algorithm
                                        will start at that date and end at the current day."""
                                            ),
                                            html.P(),
                                            dcc.DatePickerSingle(
                                                id="date-picker",
                                                min_date_allowed=date(1950, 1, 1),
                                                max_date_allowed=date(2022, 12, 5),
                                                initial_visible_month=date(2021, 1, 1),
                                                date=date(2021, 1, 1),
                                            ),
                                            html.P(),
                                            html.Center(html.Div(id="hist-period")),
                                            html.P(),
                                            dcc.Graph(id="mass-graph"),
                                        ],
                                    ),
                                ],
                                style=TABS_STYLES,
                            )
                        ]
                    )
                ]
            ),
        ]
    )

    return layout


layout = serve_layout


@callback(
    Output("hist-period", "children"),
    Output("mass-graph", "figure"),
    Input("date-picker", "date"),
)
def mass_graph(cal_date):
    cal_date = parser.parse(cal_date)
    # Defining Start and End Date
    end_date = date.today().strftime("%m/%d/%Y")
    start_date = "01/01/1900"
    # Importing Data
    spx_all = (
        si.get_data("^GSPC", start_date=start_date, end_date=end_date)["close"]
        .to_frame()
        .round(1)
    )

    # Adding Moving Averages
    from pandas.core import window

    spx_all["5DMA"] = spx_all["close"].rolling(5).mean().round(1)
    spx_all["30DMA"] = spx_all["close"].rolling(30).mean().round(1)
    spx_all = spx_all.dropna()

    # Partitioning the data
    sel_start = date(cal_date.year, cal_date.month, cal_date.day)
    spx_sel = spx_all[sel_start:end_date]
    spx_past = spx_all[:sel_start]

    # Calculating distance profile
    distance_profile = stumpy.mass(spx_sel["5DMA"], spx_past["5DMA"], normalize=True)
    # Getting index position with the minimum distance score
    idx = np.argmin(distance_profile)
    # print(f"The nearest neighbor to `spx_sel` is located at index {idx} in `spx_past`")
    date_string = f"The period between {str(spx_past.iloc[idx].name.strftime('%m/%d/%Y'))} and {str(spx_past.iloc[idx+len(spx_sel)].name.strftime('%m/%d/%Y'))} is most similar to selected pattern."
    print()

    # Since MASS computes z-normalized Euclidean distances, we should z-normalize our subsequences before plotting
    spx_sel_z_norm = pd.DataFrame(stumpy.core.z_norm(spx_sel["5DMA"].values))
    add = 200
    spx_past_z_norm = pd.DataFrame(
        stumpy.core.z_norm(spx_past["5DMA"].values[idx : idx + len(spx_sel) + add])
    )

    fig = px.line(spx_sel_z_norm, labels={"index": "Days", "value": "5DMA"})
    fig.add_trace(go.Scatter(x=spx_past_z_norm.index, y=spx_past_z_norm[0]))
    fig.update_layout(
        template="plotly_dark",
        showlegend=False,
        margin=dict(b=20, t=50, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_traces(connectgaps=True),
    fig.update_xaxes(showgrid=False),
    fig.update_yaxes(showgrid=False),

    return date_string, fig
