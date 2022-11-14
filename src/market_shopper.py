# Data manipulation libraries
import numpy as np
import pandas as pd
import boto3
import s3fs

# Dashboard-related libraries
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import dash_auth

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import flask

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "22rem",
    "padding": "2rem 1rem",
    # "background-color": "#f8f9fa",
    "color": "white"
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "22rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

TABS_STYLES = {
    'height': '44px'
}
TAB_STYLE = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold',
    'backgroundColor': '#787878'
}

TAB_SELECTED_STYLE = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

# ######################
# ### BEGIN APP LAYOUT #
# ######################

app = dash.Dash(external_stylesheets=[dbc.themes.SUPERHERO], suppress_callback_exceptions=True)
app.title = "Market Shopper"
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)
server = app.server

# Sidebar implemention
sidebar = html.Div([
    html.H2("DashBoard", className="display-4"),
    html.Hr(),
    dbc.Nav([
        dbc.NavLink("Home", href="/", active="exact"),
        dbc.NavLink("Portfolio", href="/spx-main", active="exact"),
        dbc.NavLink("Equity Market Analytics", href="/qqq-main", active="exact"),
        dbc.NavLink("Bond Analytics", href="/r2k-main", active="exact"),
        dbc.NavLink("Economic Data", href="/crypto-main", active="exact"),
        dbc.NavLink("Market Signal Analysis", href="/credit-main", active="exact"),
        vertical = True,
                   pills = True)],
style = SIDEBAR_STYLE,)


# S&P 500 Analytics main page
spx_main_page = html.Div(children=[
    html.Br(),
    html.Div(children=[
        html.H2('Portfolio'),
        html.Hr(),
        html.Div(children=[
            dcc.Tabs(children=[
                dcc.Tab(id='spx-ml-tab', label='ML/DL Analysis', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='spx-vol-tab', label='Volatility Markets', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE, children=[
                        html.P(),
                        dbc.Row(children=[
                            html.P(),
                            dbc.Col(children=[
                                dcc.RadioItems(id='sp-vol-radio', value='2',
                                               options=[{'label': i, 'value': j} for i, j in
                                                        [('1m', '.0833'), ('6m', '.5'),
                                                         ('1y', '1'), ('2y', '2'),
                                                         ('5y', '5'), ('Max', 'Max')]],
                                               style={'marginLeft': '500px'},
                                               labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
                        ]),
                        html.P(),
                        dbc.Row(children=[
                            dbc.Col(dcc.Graph(id='sp-vix-vol-graph')),
                            dbc.Col(dcc.Graph(id='sp-vvix-vix-graph')),
                        ]),

                        dbc.Row(children=[
                            dbc.Col(dcc.Graph(id='sp-vix-skew-graph')),
                            dbc.Col(dcc.Graph(id='sp-vix-vxn-graph'))
                        ]),
                    ]),
                dcc.Tab(id='spx-corr-tab', label='Correlations', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
                        children=[
                            html.P(),
                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.RadioItems(id='sp-corr-radio', value='2',
                                                   options=[{'label': i, 'value': j} for i, j in
                                                            [('1m', '.0833'), ('6m', '.5'),
                                                             ('1y', '1'), ('2y', '2'),
                                                             ('5y', '5'), ('Max', 'Max')]],
                                                   style={'marginLeft': '500px'},
                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
                            ]),
                            html.P(),
                            dbc.Row(children=[
                                dbc.Col(dcc.Graph(id='sp-corr-20d-graph')),
                                dbc.Col(dcc.Graph(id='sp-corr-20d-change'))
                            ])
                        ]),
                dcc.Tab(id='spx-tech-tab', label='Technicals', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE,
                        children=[
                            html.P(),
                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.RadioItems(id='sp-tech-radio', value='2',
                                                   options=[{'label': i, 'value': j} for i, j in
                                                            [('1m', '.0833'), ('6m', '.5'),
                                                             ('1y', '1'), ('2y', '2'),
                                                             ('5y', '5'), ('Max', 'Max')]],
                                                   style={'marginLeft': '500px'},
                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
                            ]),
                            html.P(),
                            dbc.Row(children=[
                                dbc.Col(dcc.Graph(id='sp-tech-rsi-graph')),
                                dbc.Col(dcc.Graph(id='sp-tech-sma-graph'))
                            ])
                        ])
            ], style=TABS_STYLES)
        ])
    ])
])

# Nasdaq 100 Analytics main page
qqq_main_page = html.Div(children=[
    html.Br(),
    html.Div(children=[
        html.H2('Nasdaq 100 Analytics'),
        html.Hr(),
        html.Div(children=[
            dcc.Tabs(children=[
                dcc.Tab(id='qqq-ml-tab', label='ML/DL Analysis', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='qqq-vol-tab', label='Volatility Markets', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='qqq-corr-tab', label='Correlations', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='qqq-tech-tab', label='Technicals', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE)
            ], style=TABS_STYLES)
        ])
    ])
])

# Russell 2000 Analytics main page
r2k_main_page = html.Div(children=[
    html.Br(),
    html.Div(children=[
        html.H2('Russell 2000 Analytics'),
        html.Hr(),
        html.Div(children=[
            dcc.Tabs(children=[
                dcc.Tab(id='r2k-ml-tab', label='ML/DL Analysis', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='r2k-vol-tab', label='Volatility Markets', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='r2k-corr-tab', label='Correlations', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='r2k-tech-tab', label='Technicals', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE)
            ], style=TABS_STYLES)
        ])
    ])
])

# Credit Market Analytics main page
credit_main_page = html.Div(children=[
    html.Br(),
    html.Div(children=[
        html.H2('Credit Market Analytics'),
        html.Hr(),
        html.Div(children=[
            dcc.Tabs(children=[
                dcc.Tab(id='credit-treas-tab', label='Treasury Markets', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE, children=[
                        html.Div(children=[

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.RadioItems(id='credit-treas-radio', value='2',
                                                   options=[{'label': i, 'value': j} for i, j in
                                                            [('1m', '.0833'), ('6m', '.5'),
                                                             ('1y', '1'), ('2y', '2'),
                                                             ('5y', '5'), ('Max', 'Max')]],
                                                   style={'marginLeft': '150px'},
                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
                                dbc.Col(children=[
                                    dcc.Checklist(id='credit-treas-indices', value=['SPX'],
                                                  options=[{'label': x, 'value': y}
                                                           for x, y in [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
                                                  style={'marginLeft': '250px'},
                                                  labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-2yr-graph')]),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-5yr-graph')])]),

                            html.Hr(),

                            dbc.Row(children=[
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-10yr-graph')]),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-30yr-graph')])]),

                            html.Hr(),

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-5yrreal-graph')]),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-10yrreal-graph')])])])]),

                dcc.Tab(id='credit-curves-tab', label='Treasury Curves', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE, children=[
                        html.Div(children=[
                            dbc.Row(children=[

                                dbc.Row(children=[
                                    html.P(),
                                    dbc.Col(children=[
                                        dcc.RadioItems(id='credit-curve-radio', value='2',
                                                       options=[{'label': i, 'value': j} for i, j in
                                                                [('1m', '.0833'), ('6m', '.5'),
                                                                 ('1y', '1'), ('2y', '2'),
                                                                 ('5y', '5'), ('Max', 'Max')]],
                                                       style={'marginLeft': '150px'},
                                                       labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
                                    dbc.Col(children=[
                                        dcc.Checklist(id='credit-curve-indices', value=['SPX'],
                                                      options=[{'label': x, 'value': y}
                                                               for x, y in [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
                                                      style={'marginLeft': '250px'},
                                                      labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),

                                html.P(),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-curve-2s10s')]),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-curve-2s30s')])]),

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-curve-5s10s')]),

                                dbc.Col(children=[
                                    dcc.Graph(id='credit-curve-10s30s')])])])]),

                dcc.Tab(id='credit-corp-tab', label='Corporate Credit Markets', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE, children=[
                        html.Div(children=[

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.RadioItems(id='credit-corp-radio', value='2',
                                                   options=[{'label': i, 'value': j} for i, j in
                                                            [('1m', '.0833'), ('6m', '.5'),
                                                             ('1y', '1'), ('2y', '2'),
                                                             ('5y', '5'), ('Max', 'Max')]],
                                                   style={'marginLeft': '150px'},
                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
                                dbc.Col(children=[
                                    dcc.Checklist(id='credit-corp-indices', value=['SPX'],
                                                  options=[{'label': x, 'value': y}
                                                           for x, y in [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
                                                  style={'marginLeft': '250px'},
                                                  labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.Graph(id='credit-corp-rates-graph')]),

                                html.Hr(),
                                html.P(),
                                dbc.Row(children=[
                                    dbc.Col(children=[
                                        dcc.Graph(id='HY-minus-A-graph')]),
                                    dbc.Col(children=[
                                        dcc.Graph(id='BBB-minus-A-graph')])]),

                                html.Hr(),

                                dbc.Row(children=[
                                    html.P(),
                                    dbc.Col(children=[
                                        dcc.Graph('BB-minus-BBB-graph')]),
                                    dbc.Col(children=[
                                        dcc.Graph('CCC-minus-BB-graph')])])])])]),

                dcc.Tab(id='credit-addl-tab', label='Additional Metrics', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE),
            ], style=TABS_STYLES)
        ])
    ])
])

# Econ Data main page
econ_main_page = html.Div(children=[
    html.Br(),
    html.Div(children=[
        html.H2('Economic Data & Analytics'),
        html.Hr(),
        html.Div(children=[
            dcc.Tabs(children=[
                dcc.Tab(id='econ-emp-tab', label='Employment Indicators', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE, children=[
                        html.Div(children=[

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.RadioItems(id='econ-emp-radio', value='2',
                                                   options=[{'label': i, 'value': j} for i, j in
                                                            [('1m', '.0833'), ('6m', '.5'),
                                                             ('1y', '1'), ('2y', '2'),
                                                             ('5y', '5'), ('Max', 'Max')]],
                                                   style={'marginLeft': '150px'},
                                                   labelStyle={'font-size': '20px', 'padding': '.5rem'})], ),
                                dbc.Col(children=[
                                    dcc.Checklist(id='econ-emp-indices', value=['SPX'],
                                                  options=[{'label': x, 'value': y}
                                                           for x, y in [('S&P 500', 'SPX'), ('NASDAQ', 'QQQQ')]],
                                                  style={'marginLeft': '250px'},
                                                  labelStyle={'font-size': '20px', 'padding': '.5rem'})])], ),

                            dbc.Row(children=[
                                dbc.Col(children=[
                                    dcc.Graph(id='econ-emp-nonfarm-graph')]),
                                dbc.Col(children=[
                                    dcc.Graph(id='econ-emp-claims-graph')])]),

                            html.Hr(),

                            dbc.Row(children=[
                                html.P(),
                                dbc.Col(children=[
                                    dcc.Graph('econ-emp-labor-graph')]),
                                dbc.Col(children=[
                                    dcc.Graph('econ-emp-unemp-graph')])])])]),

                dcc.Tab(id='econ-inflation-tab', label='Inflation Indicators', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='econ-activity-tab', label='Activity Indicators', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE),
                dcc.Tab(id='eocn-housing-tab', label='Housing Indicators', style=TAB_STYLE,
                        selected_style=TAB_SELECTED_STYLE),
            ], style=TABS_STYLES)
        ])
    ])
])

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

             ######################
             ### BEGIN CALLBACKS  #
             ######################

             # Callback to control render of pages given sidebar navigation
             @ app.callback(Output("page-content", "children"),
                            [Input("url", "pathname")])


def render_page_content(pathname):
    if pathname == "/home":
        return html.P("This is the content of the home page!")
    elif pathname == "/spx-main":
        return spx_main_page
    elif pathname == "/qqq-main":
        return qqq_main_page
    elif pathname == "/r2k-main":
        return r2k_main_page
    elif pathname == "/crypto-main":
        return html.P('Crypto main page')
    elif pathname == "/credit-main":
        return credit_main_page
    elif pathname == "/econ-main":
        return econ_main_page

    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


def generate_line_graph(df, x, y, title, window, indices):
    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig = fig.add_trace(go.Scatter(x=df[x], y=df[y], name=y))
    fig.update_layout(title=dict(text=title, x=.5, xanchor='center'), template='plotly_dark',
                      showlegend=False, margin=dict(b=20, t=50, l=40, r=20), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)')

    if indices != None:
        for index in indices:
            fig.add_trace(go.Scatter(x=df['date'], y=df[index], name=index), secondary_y=True)

    fig.update_traces(connectgaps=True)

    return fig


### Credit tab callbacks
@app.callback(Output('credit-2yr-graph', 'figure'),
              [Input('credit-treas-radio', 'value'),
               Input('credit-treas-indices', 'value')])
def credit_treas_2yr_graph(window, indices):
    df = main_df
    x = 'date'
    y = '2yTreas'
    title = '2yr Treasuries'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-5yr-graph', 'figure'),
              [Input('credit-treas-radio', 'value'),
               Input('credit-treas-indices', 'value')])
def credit_treas_5yr_graph(window, indices):
    df = main_df
    x = 'date'
    y = '5yTreas'
    title = '5yr Treasuries'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-10yr-graph', 'figure'),
              [Input('credit-treas-radio', 'value'),
               Input('credit-treas-indices', 'value')])
def credit_treas_10yr_graph(window, indices):
    df = main_df
    x = 'date'
    y = '10yTreas'
    title = '10yr Treasuries'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-30yr-graph', 'figure'),
              [Input('credit-treas-radio', 'value'),
               Input('credit-treas-indices', 'value')])
def credit_treas_30yr_graph(window, indices):
    df = main_df
    x = 'date'
    y = '30yTreas'
    title = '30yr Treasuries'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-5yrreal-graph', 'figure'),
              [Input('credit-treas-radio', 'value'),
               Input('credit-treas-indices', 'value')])
def credit_treas_5yrreal_graph(window, indices):
    df = main_df
    x = 'date'
    y = '5yrReal'
    title = '5yr Treasury Real Rate'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-10yrreal-graph', 'figure'),
              [Input('credit-treas-radio', 'value'),
               Input('credit-treas-indices', 'value')])
def credit_treas_10yrreal_graph(window, indices):
    df = main_df
    x = 'date'
    y = '10yrReal'
    title = '10yr Treasury Real Rate'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-curve-2s10s', 'figure'),
              [Input('credit-curve-radio', 'value'),
               Input('credit-curve-indices', 'value')])
def credit_treas_2s10s_graph(window, indices):
    df = main_df
    x = 'date'
    y = '2s10s'
    title = '2s10s Treasury Curve'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-curve-2s30s', 'figure'),
              [Input('credit-curve-radio', 'value'),
               Input('credit-curve-indices', 'value')])
def credit_treas_2s30s_graph(window, indices):
    df = main_df
    x = 'date'
    y = '2s30s'
    title = '2s30s Treasury Curve'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-curve-5s10s', 'figure'),
              [Input('credit-curve-radio', 'value'),
               Input('credit-curve-indices', 'value')])
def credit_treas_5s10s_graph(window, indices):
    df = main_df
    x = 'date'
    y = '5s10s'
    title = '5s10s Treasury Curve'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-curve-10s30s', 'figure'),
              [Input('credit-curve-radio', 'value'),
               Input('credit-curve-indices', 'value')])
def credit_treas_10s30s_graph(window, indices):
    df = main_df
    x = 'date'
    y = '10s30s'
    title = '10s30s Treasury Curve'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('HY-minus-A-graph', 'figure'),
              [Input('credit-corp-radio', 'value'),
               Input('credit-corp-indices', 'value')])
def credit_treas_hy_minus_a_graph(window, indices):
    df = main_df
    x = 'date'
    y = 'HY_minus_A'
    title = 'HY vs A OAS'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('BBB-minus-A-graph', 'figure'),
              [Input('credit-corp-radio', 'value'),
               Input('credit-corp-indices', 'value')])
def credit_treas_bbb_minus_a_graph(window, indices):
    df = main_df
    x = 'date'
    y = 'BBB_minus_A'
    title = 'BBB vs A OAS'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('BB-minus-BBB-graph', 'figure'),
              [Input('credit-corp-radio', 'value'),
               Input('credit-corp-indices', 'value')])
def credit_treas_bb_minus_bbb_graph(window, indices):
    df = main_df
    x = 'date'
    y = 'BB_minus_BBB'
    title = 'BB vs BBB OAS'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('CCC-minus-BB-graph', 'figure'),
              [Input('credit-corp-radio', 'value'),
               Input('credit-corp-indices', 'value')])
def credit_treas_ccc_minus_bb_graph(window, indices):
    df = main_df
    x = 'date'
    y = 'CCC_minus_BB'
    title = 'CCC vs BB OAS'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('credit-corp-rates-graph', 'figure'),
              [Input('credit-corp-radio', 'value')])
def sp_vvix_vix_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'AOAS'
    title = 'Corporate Credit OAS By Rating'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['BBBOAS'], name='BBB'))
    fig.add_trace(go.Scatter(x=df['date'], y=df['BBOAS'], name='BB'))
    fig.add_trace(go.Scatter(x=df['date'], y=df['BOAS'], name='B'))
    fig.add_trace(go.Scatter(x=df['date'], y=df['CCCOAS'], name='CCC'))
    fig.update_layout(showlegend=True)
    fig.update_traces(connectgaps=True)

    return fig


# SPX Tab callbacks

@app.callback(Output('sp-vix-vol-graph', 'figure'),
              [Input('sp-vol-radio', 'value')])
def sp_vix_vol_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = '^VIX'
    title = 'VIX & VVIX'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['^VVIX']), secondary_y=True)
    return fig


@app.callback(Output('sp-vvix-vix-graph', 'figure'),
              [Input('sp-vol-radio', 'value')])
def sp_vvix_vix_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'vix_diff_sma'
    title = '10 Day Smoothed, Normalized VVIX-VIX'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['SPX']), secondary_y=True)
    return fig


@app.callback(Output('sp-vix-skew-graph', 'figure'),
              [Input('sp-vol-radio', 'value')])
def sp_vix_move_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = '^SKEW'
    title = 'S&P500 Option Skew'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['SPX']), secondary_y=True)
    return fig


@app.callback(Output('sp-vix-vxn-graph', 'figure'),
              [Input('sp-vol-radio', 'value')])
def sp_vix_vxn_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'VXN_minus_VIX'
    title = 'VXN / VIX Ratio'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['SPX']), secondary_y=True)
    return fig


@app.callback(Output('sp-corr-20d-graph', 'figure'),
              [Input('sp-corr-radio', 'value')])
def sp_corr_20d_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'SPX_20D_corr'
    title = 'S&P 500 Constituent 20D Correlation'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
    return fig


@app.callback(Output('sp-corr-20d-change', 'figure'),
              [Input('sp-corr-radio', 'value')])
def sp_corr_20d_change(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'SPX_20D_corr_delta'
    title = 'S&P 500 Constituent 20D Correlation Delta'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
    return fig


@app.callback(Output('sp-tech-rsi-graph', 'figure'),
              [Input('sp-tech-radio', 'value')])
def sp_vix_vol_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'SPX_RSI'
    title = '10D Smoothed RSI'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
    return fig


@app.callback(Output('sp-tech-sma-graph', 'figure'),
              [Input('sp-tech-radio', 'value')])
def sp_vix_vol_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'SPX_pct_over_200sma'
    title = 'SPX Position Relative to 200D SMA'
    fig = generate_line_graph(df, x, y, title, window, indices)
    fig.add_trace(go.Scatter(x=df['date'], y=df['SPX'], name='SPX'), secondary_y=True)
    return fig


# ECON Callbacks
@app.callback(Output('econ-emp-nonfarm-graph', 'figure'),
              [Input('econ-emp-radio', 'value'),
               Input('econ-emp-indices', 'value')])
def econ_emp_nonfarm_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'Non-Farm Payrolls'
    title = 'Non-Farm Payrolls'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('econ-emp-claims-graph', 'figure'),
              [Input('econ-emp-radio', 'value'),
               Input('econ-emp-indices', 'value')])
def econ_emp_claims_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'Initial Claims'
    title = 'Initial Claims'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('econ-emp-labor-graph', 'figure'),
              [Input('econ-emp-radio', 'value'),
               Input('econ-emp-indices', 'value')])
def econ_emp_labor_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'Labor_Force_Rate'
    title = 'Labor Force Participation Rate'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


@app.callback(Output('econ-emp-unemp-graph', 'figure'),
              [Input('econ-emp-radio', 'value'),
               Input('econ-emp-indices', 'value')])
def econ_emp_unemp_graph(window, indices=None):
    df = main_df

    if window == 'Max':
        df = df
    elif window == '.5':
        window = 126
        df = df.tail(126)
    elif window == '.0833':
        window = 20
        df = df.tail(20)
    else:
        window = int(window) * 252
        df = df.tail(window)

    x = 'date'
    y = 'Unenmployment'
    title = 'Unemployment Rate'
    fig = generate_line_graph(df, x, y, title, window, indices)
    return fig


if __name__ == "__main__":
    s3_client = boto3.client('s3',
                             aws_access_key_id='',
                             aws_secret_access_key='',
                             region_name='us-east-1')

    s3_client.download_file('riskboard-bucket', 'model_data.csv', 'model_data.csv')
    print('Loaded data from S3')
    main_df = pd.read_csv('model_data.csv')
    main_df['date'] = main_df.index
    print(main_df.columns)
    # main_df = pd.read_csv('assets/df.csv')
    app.run_server(debug=True)
