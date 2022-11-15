import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from src.utils import generate_line_graph
import datetime as dt
from datetime import date
from src import create_dashboard
from src import create_dashboard, create_app
import plotly.express as px

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import src.data.yahoo as yahoo
from dash import dash_table
import pandas as pd

# from src.visualization import home

dash.register_page(__name__, path="/", order=1)

# layout = dbc.Col(dbc.Col(children=html.P("This is a test.")))

# sp500 = yahoo.retrieve_company_stock_price_from_mongo("DT")

# layout = dash_table.DataTable(sp500.to_dict('records'), [{"name": i, "id": i} for i in sp500.columns])

# layout = dbc.Col(children=dcc.Graph(figure=home.create_indices_chart()))
# layout = dbc.Col(children=dcc.Graph(id='indices_chart'))

df = yahoo.retrieve_company_stock_price_from_mongo("MSFT")
df = df["stock_price"]
df = pd.DataFrame(df)

layout = html.Div(
    [
        dcc.Graph(id="indices_chart"),
        # dcc.Slider(
        #     df["Date"].min(),
        #     df["Date"].max(),
        #     step=None,
        #     value=df["Date"].min(),
        #     marks={str(year): str(year) for year in df["Date"].unique()},
        #     id="year-slider",
        # ),
    ]
)


@callback(Output("indices_chart", "figure"), Input("year-slider", "value"))
def indices_chart(window, indices=None):
    # df = yahoo.retrieve_company_stock_price_from_mongo("MSFT")
    # fig = generate_line_graph(df, x, y, title, window, indices)
    fig = px.line(df, "Date", "Close", title="Industrial Averages")
    fig.update_layout(
        {"plot_bgcolor": "#e6e6e6", "paper_bgcolor": "#e6e6e6", "font_color": "black"}
    )
    fig.update_traces(line_color="#0000ff")
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=5, label="5y", step="year", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(step="all"),
                ]
            )
        )
    )
    return fig
