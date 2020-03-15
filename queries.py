import pandas as pd
import datetime

from constants import DB_CONNECTION, DATE_FORMAT

def get_past_game_ids(date_string: str) -> pd.DataFrame:
    today = datetime.datetime.strptime(date_string, DATE_FORMAT)
    minus_10 = today - datetime.timedelta(days=10)
    return pd.read_sql_query("""
                            SELECT game_id,
                                   date
                            FROM date where 
                            to_date(date, 'YYYY-MM-DD') >= to_date('{minus_10}', 'YYYY-MM-DD')
                            AND to_date(date, 'YYYY-MM-DD') <= to_date('{today}', 'YYYY-MM-DD')
                            """.format(minus_10=minus_10.strftime(DATE_FORMAT),
                                        today=today.strftime(DATE_FORMAT)),
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


def get_past_winners(date_string: str) -> pd.DataFrame:

    past_game_ids = get_past_game_ids(date_string)
    ids_as_strings = past_game_ids.game_id.astype("str").tolist()
    game_results = pd.read_sql_query("""
                                     SELECT game_id,
                                            contestant_id,
                                            SUM(change_in_value) as final_amount
                                     FROM game
                                     WHERE game_id IN ({game_ids})
                                     GROUP BY game_id, contestant_id
                                     """.format(game_ids=",".join(ids_as_strings)),
                                     DB_CONNECTION)
    winners = game_results.groupby("game_id").\
                 agg(lambda df: df.loc[df['final_amount'].idxmax()]).\
                 reset_index()
    contestants = ",".join(winners.contestant_id.astype("int").astype('str').\
                                   unique().tolist())
    contestant_info = get_contestant_info(contestants)
    winners = winners.merge(past_game_ids).merge(contestant_info)
    winners['graph_text'] = (winners['first_name'] + " " + 
                             winners['last_name'] + ", " + 
                             winners['hometown'] + ", " +
                             winners['occupation'])
    return winners[['date', 'final_amount', 'graph_text']]
    
