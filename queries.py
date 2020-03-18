import pandas as pd
import datetime
from typing import List

from constants import DB_CONNECTION, DATE_FORMAT
from utilities import get_unique_contestant_ids

def get_10_latest_games() -> pd.DataFrame:
    return pd.read_sql_query("""
                             SELECT game_id,
                                    date
                             FROM date
                             ORDER BY date desc
                             limit 10       
                             """,
                            DB_CONNECTION)


def get_contestant_info(contestant_ids: str) -> pd.DataFrame:
	return pd.read_sql_query("""
                             SELECT contestant_id,
                                    first_name,
                                    last_name,
                                    hometown,
                                    occupation
                             FROM contestant
                             WHERE contestant_id IN ({})
                             """.format(contestant_ids),
                             DB_CONNECTION)


def get_past_winners() -> pd.DataFrame:
	
	past_game_ids = get_10_latest_games()
	ids_as_string = ",".join(past_game_ids.game_id.unique().astype('str').tolist())

	game_results = pd.read_sql_query("""
									 SELECT game_id,
                                            contestant_id,
                                            SUM(change_in_value) as final_amount
                                     FROM game
                                     WHERE game_id IN ({game_ids})
                                     GROUP BY game_id, contestant_id
                                     """.format(game_ids=ids_as_string),
                                     DB_CONNECTION)
	winners = game_results.groupby("game_id").\
                 agg(lambda df: df.loc[df['final_amount'].idxmax()]).\
                 reset_index()
	contestants = get_unique_contestant_ids(winners)
	contestant_info = get_contestant_info(contestants)
	winners = winners.merge(past_game_ids).merge(contestant_info)
	winners['graph_text'] = (winners['first_name'] + " " + 
                             winners['last_name'] + ", " + 
                             winners['hometown'] + ", " +
                             winners['occupation'])
	return winners[['date', 'final_amount', 'graph_text']]


def get_game_trend(date: str) -> pd.DataFrame:

       game_id = pd.read_sql_query("""
                                   SELECT game_id
                                   FROM date
                                   WHERE date = '{date}'
                                   """.format(date=date),
                                   DB_CONNECTION)
       
       game_id = game_id.game_id.iloc[0]

       game_trend_query = """
                          SELECT contestant_id,
                          clue_order_number,
                          SUM(change_in_value) 
                          OVER (PARTITION BY contestant_id
                                ORDER BY clue_order_number asc rows between unbounded preceding and current row)
                          AS running_total
                          FROM game
                          WHERE game_id = {game_id}
                          """


       game_trend = pd.read_sql_query(game_trend_query.format(game_id=game_id),
                                      DB_CONNECTION)

       contestants = get_unique_contestant_ids(game_trend)
       contestant_info = get_contestant_info(contestants)
       game_trend = game_trend.merge(contestant_info)
       game_trend['graph_text'] = (game_trend['first_name'] + " " + 
                                   game_trend['last_name'])
       return game_trend
