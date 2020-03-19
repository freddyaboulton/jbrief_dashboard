import datetime
import os
from typing import Dict, Any

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output
from flask_caching import Cache

from queries import get_past_winners, get_game_trend, get_10_latest_games, get_question_info
from utilities import get_unique_contestant_ids
from constants import DATE_FORMAT, MILLISECONDS_BETWEEN_UPDATES

external_stylesheets = [dbc.themes.DARKLY]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

colors = {
    'darkblue': '#061E44',
    'jeopardy-yellow': '#FFCC00',
    'white': '#FFFFFF',
    'grey': '#808080'
}


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
                         interval=MILLISECONDS_BETWEEN_UPDATES,
                         n_intervals=0),
            html.Div(id='current-date', style={'display': 'none'})

            ], 
            width={'size': 6}
        ),
        dbc.Col([
            dcc.Graph(id='game-trend')
        ], width=6),
    ], justify='center'),
    dbc.Row([
        dbc.Col([], width=6),
        dbc.Col(children=[],
                 id='table',
                 width=6)
    ])
])


@app.callback(Output('latest-winners', 'figure'),
              [Input('interval', 'n_intervals')])
def update_latest_winners_graph(n) -> Dict[str, Any]:
    """
    Updates the latest winners graph every MILLISECONDS_BETWEEN_UPDATES ms.
    :param n: Number of intervals that have passed. Ignored.
    :return: Latest winners figure (left hand side).
    """

    winners = get_past_winners()
    data = [{'x': winners.date.tolist(),
             'y': winners.final_amount.tolist(),
             'text': winners.graph_text.tolist(),
             'marker': {'size': 10}
             }]
    layout = {'title': 'Latest Winners',
              'hovermode': 'closest',
              'type': 'linear',
               'xaxis': {'title': 'Date of Game',
                         'fixedrange': True,
                         'gridcolor': colors['grey']},
               'yaxis': {'title': 'Dollars Won',
                         'fixedrange': True,
                         'gridcolor': colors['grey']},
              'plot_bgcolor': colors['darkblue'],
              'paper_bgcolor': colors['darkblue'],
              'font': {'color': colors['white']}}
    return {'data': data, 'layout': layout}


@app.callback(Output('current-date', 'children'),
              [Input('latest-winners', 'clickData')])
def store_current_date(clickData) -> str:
    """
    Stores the date of the game the user clicked on so
    it can be shared by the game trend figure and question info table.
    :param clickData: The data for the point in the latest winners graph
        the user clicked on. If not clicked on a point, use the latest date.
    :return: Current date in hidden div.
    """

    if not clickData:
        # df sorted in descending order so get the first point for
        # # latest game
        past_game_ids = get_10_latest_games()
        date = past_game_ids.date.tolist()[0]
    
    else:
        date = clickData['points'][0]['x']
    
    return date


@app.callback(Output('game-trend', 'figure'),
              [Input('current-date', 'children')])
def update_game_trend_graph(date) -> Dict[str, Any]:
    """
    Updates the game trend graph given the date the user clicked on.
    :param date: Date the user clicked on formatted as %Y-%m-%d.
    :return: Game trend figure (right hand side).
    """

    game_trend = get_game_trend(date)
    contestant_ids = [int(ID) for ID in get_unique_contestant_ids(game_trend).split(",")]
    date_for_title = datetime.datetime.strptime(date, DATE_FORMAT).strftime('%b %d, %Y')

    data = [{'x': game_trend.clue_order_number.loc[game_trend.contestant_id == contestant_id].tolist(),
             'y': game_trend.running_total.loc[game_trend.contestant_id == contestant_id].tolist(),
             'name': game_trend.graph_text.loc[game_trend.contestant_id == contestant_id].tolist()[0],
             'mode': 'lines+markers'
             } for contestant_id in contestant_ids]
    layout = {'title': f'Game Trend for {date_for_title}',
              'hovermode': 'x',
              'type': 'linear',
              'xaxis': {'title': 'Number of Clues Asked In Game',
                        'dtick': 10,
                        'fixedrange': True,
                        'gridcolor': colors['grey']},
              'yaxis': {'title': 'Dollars Won',
                        'fixedrange': True,
                        'gridcolor': colors['grey']},
              'plot_bgcolor': colors['darkblue'],
              'paper_bgcolor': colors['darkblue'],
              'font': {'color': colors['white']},
             }
    return {'data': data, 'layout': layout}


@app.callback(Output('table', 'children'),
              [Input('game-trend', 'hoverData'),
               Input('current-date', 'children')])
def update_question_table(hoverData, current_date) -> dbc.Table:
    """
    Updates the question table given the point the user is
    hovering over.
    :param hoverData: The data for the point the user is hovering over.
    :param current_date: The date the user clicked on previously.
    :return: Table element.
    """

    if not hoverData:
        index = 1
    else:
        index = hoverData['points'][0]['x']
    
    return dbc.Table.from_dataframe(get_question_info(current_date, index))


if __name__ == '__main__':
    app.run_server(debug=True)
