import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from src.utils import generate_line_graph
import datetime as dt
from datetime import date
from src import create_dashboard
from src import create_dashboard, create_app

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

dash.register_page(__name__, path='/', order=1)

layout = dbc.Col(dbc.Col(children=html.P('This is a test.')))


@callback(
    Output('output-container-date-picker-range', 'children'),
    [Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')])
def update_output(start_date, end_date):
    string_prefix = 'You have selected: '
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        start_date_string = start_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        end_date_string = end_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'End Date: ' + end_date_string
    if len(string_prefix) == len('You have selected: '):
        return 'Select a date to see it displayed here'
    else:
        return string_prefix

# layout = html.Div(children=[
#     html.Br(),
#     html.Div(children=[
#         html.H2('Portfolio'),
#         html.Hr(),
#         html.Div(children=[
#             dcc.Tabs(children=[
#                 dcc.Tab(id='spx-ml-tab', label='ML/DL Analysis', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
#                 dcc.Tab(id='spx-vol-tab', label='Volatility Markets', style=TAB_STYLE,
#                         selected_style=TAB_SELECTED_STYLE, children=[
#                         html.P(),
#                         dbc.Row(children=[
#                             html.P(),
#                             dbc.Col(children=[
#                                 dcc.RadioItems(id='sp-vol-radio', value='2',
#                                                options=[{'label': i, 'value': j} for i, j in
#                                                         [('1m', '.0833'), ('6m', '.5'),
#                                                          ('1y', '1'), ('2y', '2'),
#                                                          ('5y', '5'), ('Max', 'Max')]],
#                                                style={'marginLeft': '500px'},
#                                                labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
#                         ]),
#                         html.P(),
#                         dbc.Row(children=[
#                             dbc.Col(dcc.Graph(id='sp-vix-vol-graph')),
#                             dbc.Col(dcc.Graph(id='sp-vvix-vix-graph')),
#                         ]),
#
#                         dbc.Row(children=[
#                             dbc.Col(dcc.Graph(id='sp-vix-skew-graph')),
#                             dbc.Col(dcc.Graph(id='sp-vix-vxn-graph'))
#                         ]),
#                     ]),
#                 dcc.Tab(id='spx-corr-tab', label='Correlations', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
#                         children=[
#                             html.P(),
#                             dbc.Row(children=[
#                                 html.P(),
#                                 dbc.Col(children=[
#                                     dcc.RadioItems(id='sp-corr-radio', value='2',
#                                                    options=[{'label': i, 'value': j} for i, j in
#                                                             [('1m', '.0833'), ('6m', '.5'),
#                                                              ('1y', '1'), ('2y', '2'),
#                                                              ('5y', '5'), ('Max', 'Max')]],
#                                                    style={'marginLeft': '500px'},
#                                                    labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
#                             ]),
#                             html.P(),
#                             dbc.Row(children=[
#                                 dbc.Col(dcc.Graph(id='sp-corr-20d-graph')),
#                                 dbc.Col(dcc.Graph(id='sp-corr-20d-change'))
#                             ])
#                         ]),
#                 dcc.Tab(id='spx-tech-tab', label='Technicals', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
#                         children=[
#                             html.P(),
#                             dbc.Row(children=[
#                                 html.P(),
#                                 dbc.Col(children=[
#                                     dcc.RadioItems(id='sp-tech-radio', value='2',
#                                                    options=[{'label': i, 'value': j} for i, j in
#                                                             [('1m', '.0833'), ('6m', '.5'),
#                                                              ('1y', '1'), ('2y', '2'),
#                                                              ('5y', '5'), ('Max', 'Max')]],
#                                                    style={'marginLeft': '500px'},
#                                                    labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
#                             ]),
#                             html.P(),
#                             dbc.Row(children=[
#                                 dbc.Col(dcc.Graph(id='sp-tech-rsi-graph')),
#                                 dbc.Col(dcc.Graph(id='sp-tech-sma-graph'))
#                             ])
#                         ])
#             ], style=TABS_STYLES)
#         ])
#     ])
# ])
#
#
# @app.callback(Output('sp-vix-vol-graph', 'figure'),
#               [Input('sp-vol-radio', 'value')])
# def sp_vix_vol_graph(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = '^VIX'
#     title = 'VIX & VVIX'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['^VVIX']), secondary_y=True)
#     return fig
#
#
# @app.callback(Output('sp-vvix-vix-graph', 'figure'),
#               [Input('sp-vol-radio', 'value')])
# def sp_vvix_vix_graph(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = 'vix_diff_sma'
#     title = '10 Day Smoothed, Normalized VVIX-VIX'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['SPX']), secondary_y=True)
#     return fig
#
#
# @app.callback(Output('sp-vix-skew-graph', 'figure'),
#               [Input('sp-vol-radio', 'value')])
# def sp_vix_move_graph(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = '^SKEW'
#     title = 'S&P500 Option Skew'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['SPX']), secondary_y=True)
#     return fig
#
#
# @app.callback(Output('sp-vix-vxn-graph', 'figure'),
#               [Input('sp-vol-radio', 'value')])
# def sp_vix_vxn_graph(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = 'VXN_minus_VIX'
#     title = 'VXN / VIX Ratio'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['SPX']), secondary_y=True)
#     return fig
#
#
# @app.callback(Output('sp-corr-20d-graph', 'figure'),
#               [Input('sp-corr-radio', 'value')])
# def sp_corr_20d_graph(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = 'SPX_20D_corr'
#     title = 'S&P 500 Constituent 20D Correlation'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
#     return fig
#
#
# @app.callback(Output('sp-corr-20d-change', 'figure'),
#               [Input('sp-corr-radio', 'value')])
# def sp_corr_20d_change(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = 'SPX_20D_corr_delta'
#     title = 'S&P 500 Constituent 20D Correlation Delta'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
#     return fig
#
#
# @app.callback(Output('sp-tech-rsi-graph', 'figure'),
#               [Input('sp-tech-radio', 'value')])
# def sp_vix_vol_graph(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = 'SPX_RSI'
#     title = '10D Smoothed RSI'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
#     return fig
#
#
# @app.callback(Output('sp-tech-sma-graph', 'figure'),
#               [Input('sp-tech-radio', 'value')])
# def sp_vix_vol_graph(window, indices=None):
#     df = main_df
#
#     if window == 'Max':
#         df = df
#     elif window == '.5':
#         window = 126
#         df = df.tail(126)
#     elif window == '.0833':
#         window = 20
#         df = df.tail(20)
#     else:
#         window = int(window) * 252
#         df = df.tail(window)
#
#     x = 'date'
#     y = 'SPX_pct_over_200sma'
#     title = 'SPX Position Relative to 200D SMA'
#     fig = generate_line_graph(df, x, y, title, window, indices)
#     fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
#     return fig
