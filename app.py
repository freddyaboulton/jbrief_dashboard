import datetime
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output
from flask_caching import Cache

from queries import get_past_winners, get_game_trend, get_10_latest_games
from utilities import get_unique_contestant_ids
from constants import DATE_FORMAT

external_stylesheets = [dbc.themes.DARKLY]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get("REDIS_URL", 'redis://localhost:6379')
}
cache = Cache()
cache.init_app(server, config=CACHE_CONFIG)

colors = {
    'darkblue': '#061E44',
    'jeopardy-yellow': '#FFCC00',
    'white': '#FFFFFF',
    'grey': '#808080'
}


@cache.memoize()
def get_past_game_ids_df(key: str) -> pd.DataFrame:
    assert 'past-games_' in key, f"get_past_game_ids_df key not properly formatted {key}."
    return get_10_latest_games()


@cache.memoize()
def get_winners_df(key: str) -> pd.DataFrame:
    assert "winners_" in key, f"get_winners_df key not properly formatted {key}."
    return get_past_winners()


@cache.memoize()
def get_game_trend_df(key: str) -> pd.DataFrame:
    assert "game-trend_" in key, f'get_game_trend key not properly formatted {key}.'
    game_id = key.split("_")[1]
    return get_game_trend(game_id)


app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('JBrief')
        ],
        width={'size': 8, 'offset': 2},
        style={'textAlign': 'center',
               'color': colors['white']}),
    dbc.Col([
        html.A([
            html.Img(src='assets/github_logo.png',
                     style={'height': '40%', 'width': '40%',
                            'margin': '12px',
                            'textAlign': 'right'})
            ],
            href='https://github.com/freddyaboulton/jbrief_dashboard',
            )
        ],
         width=1),
    ]),

    html.H4(['Jeopardy games at a glance'],
    style={"textAlign": 'center',
            'color': colors['white']}),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='latest-winners'),
            dcc.Interval(id='interval',
                         interval=1*1000,
                         n_intervals=0)
            ], 
            width={'size': 6}
        ),
        dbc.Col([
            dcc.Graph(id='game-trend')
        ], width=6),
    ], justify='center')
])


@app.callback(Output('latest-winners', 'figure'),
              [Input('interval', 'n_intervals')])
def update_latest_winners_graph(n):
    todays_date = datetime.datetime.now().strftime(DATE_FORMAT)
    winners = get_winners_df(f'winners_{todays_date}')
    data = [{'x': winners.date.tolist(),
             'y': winners.final_amount.tolist(),
             'text': winners.graph_text.tolist(),
             'marker': {'size': 10}
             }]
    layout = {'title': 'Latest Winners',
              'hovermode': 'closest',
              'type': 'linear',
               'xaxis': {'title': 'Date of Game',
                         'gridcolor': colors['grey']},
               'yaxis': {'title': 'Dollars Won',
                         'gridcolor': colors['grey']},
              'plot_bgcolor': colors['darkblue'],
              'paper_bgcolor': colors['darkblue'],
              'font': {'color': colors['white']}}
    return {'data': data, 'layout': layout}


@app.callback(Output('game-trend', 'figure'),
              [Input('latest-winners', 'clickData')])
def update_game_trend_graph(clickData):
    todays_date = datetime.datetime.now().strftime(DATE_FORMAT)
    past_game_ids = get_past_game_ids_df(f'past-games_{todays_date}')

    if not clickData:
        # df sorted in descending order so get the first point for
        # latest game
        date = past_game_ids.date.tolist()[0]
    else:
        date = clickData['points'][0]['x']

    game_trend = get_game_trend_df(f'game-trend_{date}')
    contestant_ids = [int(ID) for ID in get_unique_contestant_ids(game_trend).split(",")]

    data = [{'x': game_trend.clue_order_number.loc[game_trend.contestant_id == contestant_id].tolist(),
             'y': game_trend.running_total.loc[game_trend.contestant_id == contestant_id].tolist(),
             'name': game_trend.graph_text.loc[game_trend.contestant_id == contestant_id].tolist()[0],
             'mode': 'lines+markers'
             } for contestant_id in contestant_ids]
    layout = {'title': f'Game Trend for {date}',
              'type': 'linear',
              'xaxis': {'title': 'Number of Clues Asked In Game',
                        'dtick': 10,
                        'gridcolor': colors['grey']},
              'yaxis': {'title': 'Dollars Won In Game',
                        'gridcolor': colors['grey']},
              'plot_bgcolor': colors['darkblue'],
              'paper_bgcolor': colors['darkblue'],
              'font': {'color': colors['white']},
             }
    return {'data': data, 'layout': layout}


if __name__ == '__main__':
    app.run_server(debug=True)
