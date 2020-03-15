import datetime
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
from flask_caching import Cache

from queries import get_past_winners
from constants import DATE_FORMAT

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash("jbrief", external_stylesheets=external_stylesheets)
server = app.server

CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get("REDIS_URL", 'redis://localhost:6379')
}
cache = Cache()
cache.init_app(server, config=CACHE_CONFIG)

@cache.memoize()
def get_winners_df(key):
    assert "winners_" in key, f"get_winners_df key not properly formatted {key}"
    date = key.split("_")[1]
    return get_past_winners(date)

app.layout = html.Div(
    children=[
    html.H1(children='Jbrief',
            style={"color": '#7FDBFF',
                   'textAlign': 'center'}),
    html.Div(children='''
        Jeopardy games at a glance
    ''',
            style={"textAlign": 'center'}),
    html.Div([
        html.Div([
            dcc.Graph(id='latest-winners'),
            dcc.Interval(id='interval',
                         interval=1*1000,
                         n_intervals=0)
        ], className='six columns'),
        html.Div([
            dcc.Graph(
                id='example-graph-2',
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'Foo'},
                        {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': 'Bar'},
                    ],
                    'layout': {
                        'title': 'Plot 2',
                        'plot_bgcolor': "#111111",
                        'paper_bgcolor': '#111111',
                        'font': {'color': '#7FDBFF'}
                    }
                }
                )
        ], className='six columns'),
    ])
])

@app.callback(Output('latest-winners', 'figure'),
              [Input('interval', 'n_intervals')])
def update_latest_winners_graph(n):
    winners = get_winners_df(f'winners_{datetime.datetime.now().strftime(DATE_FORMAT)}')
    data = [{'x': winners.date.tolist(),
             'y': winners.final_amount.tolist(),
             'text': winners.graph_text.tolist()}]
    layout = {'title': 'Latest Winners',
              'hovermode': 'closest',
              'type': 'linear',
              'xaxis': {'tickmode': 'array',
                        'tickvals': pd.date_range(winners.date.min(),
                                              winners.date.max()).tolist()
                        },
              'plot_bgcolor': "#111111",
              'paper_bgcolor': '#111111',
              'font': {'color': '#7FDBFF'}}
    return {'data': data, 'layout': layout}

if __name__ == '__main__':
    app.run_server(debug=True)
