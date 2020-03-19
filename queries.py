import datetime
from functools import lru_cache
from typing import List

import pandas as pd

from constants import DATE_FORMAT, DB_CONNECTION
from utilities import get_unique_contestant_ids


@lru_cache(maxsize=1)
def get_10_latest_games() -> pd.DataFrame:
	""" Gets the 10 latest dates and game ids as a dataframe. """
	return pd.read_sql_query("""
							 SELECT game_id,
                                    date
                             FROM date
                             ORDER BY date desc
                             limit 10       
                             """,
                            DB_CONNECTION)


@lru_cache(maxsize=10)
def get_contestant_info(contestant_ids: str) -> pd.DataFrame:
	"""
	Gets the contestant info for a comma-separated string of
	contestant ids.
	:param contestant_ids: Comma separated string of contestant
		ids.
	:return: Contestant info as dataframe.
	"""
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


@lru_cache(maxsize=1)
def get_past_winners() -> pd.DataFrame:
	""" Gets the winners of the 10 latest games. """
	
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


@lru_cache(maxsize=10)
def get_game_id_for_date(date: str) -> str:
	"""
	For a date, map it to the internal game_id.
	:param date: Date of game formatted as %Y-%m-%d.
	:return: Game id.
	"""
	game_id = pd.read_sql_query("""
                                SELECT game_id
                                FROM date
                                WHERE date = '{date}'
                                """.format(date=date),
                                DB_CONNECTION)
	return game_id.game_id.iloc[0]


@lru_cache(maxsize=10)
def get_game_trend(date: str) -> pd.DataFrame:
	"""
	Gets the game trend (change in value over time) for each contestant
	for a point the user clicked on.
	:param date: The date for the game formatted as %Y-%m-%d.
	:return: The game trend as a dataframe.
	"""

	game_id = get_game_id_for_date(date)

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


@lru_cache(maxsize=10)
def get_questions_for_game(date: str) -> pd.DataFrame:
	"""
	Retrieves the questions and contestant info for a given
	game.
	:param date: The date for the game.
	:return: DataFrame with the question and contestant info.
	"""
       
	game_id = get_game_id_for_date(date)

	game = pd.read_sql_query("""
				    SELECT question_id,
						   clue_order_number,
					       contestant_id,
						   change_in_value
				    FROM game
				    WHERE game_id = {game_id}
				    """.format(game_id=game_id),
				    DB_CONNECTION)
	questions = pd.read_sql_query("""
                            SELECT question_id,
								   text,
						           answer,
						           is_dd
                            FROM question
                            WHERE game_id = {game_id}
                            """.format(game_id=game_id),
                            DB_CONNECTION)
	
	contestant_info = get_contestant_info(get_unique_contestant_ids(game))
	
	return questions.merge(game).merge(contestant_info)


@lru_cache(maxsize=10)
def get_question_info(date: str, clue_index: int) -> pd.DataFrame:
	"""
	Retrieves the question text and the contestants who answered it for
	a point the user hovers over.
	:param date: The date of the game.
	:param clue_index: The index of the question/clue to retrieve.
	:return: Dataframe with the question and contestant information.
	"""

	questions = get_questions_for_game(date)

	questions = questions.loc[questions.clue_order_number == clue_index]

	mask = questions.applymap(type) != bool
	d = {True: 'TRUE', False: 'FALSE'}

	questions = questions.where(mask, questions.replace(d))
	questions['name'] = (questions['first_name'] + " " + 
                             questions['last_name'])
	
	questions = questions.rename(columns={'clue_order_number': 'Index',
							  			  'text': 'Question',
										  'answer': 'Answer',
										  'is_dd': 'Daily Double',
										  'name': 'Contestant',
										  'change_in_value': "Dollars Won"})

	return questions[['Index', 'Question', 'Answer',
					  'Daily Double', 'Contestant', 'Dollars Won']]
