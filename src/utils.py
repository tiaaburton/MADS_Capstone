import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import json


def create_portfolio(seed: str, csv_portfolio_fname: str) -> json:
    portfolio = {
        'seed': seed,
        'override_accounts': []
    }

    data = pd.read_csv(csv_portfolio_fname)

    return data, portfolio


def generate_line_graph(df, x, y, title, window, indices):
    if window == "Max":
        df = df
    elif window == ".5":
        window = 126
        df = df.tail(126)
    elif window == ".0833":
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig = fig.add_trace(go.Scatter(x=df[x], y=df[y], name=y))
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center"),
        template="plotly_dark",
        showlegend=False,
        margin=dict(b=20, t=50, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    if indices != None:
        for index in indices:
            fig.add_trace(
                go.Scatter(x=df["date"], y=df[index], name=index), secondary_y=True
            )

    fig.update_traces(connectgaps=True)

    return fig

