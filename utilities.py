from typing import List
import pandas as pd


def get_unique_contestant_ids(df: pd.DataFrame) -> List[str]:
    """
    Get unique contestant ids as a comma separated list.
    :param df: Dataframe with contestant_id as a column name.
    """

    # Need to convert to int because pandas may interpret as float.
    return ",".join(df.contestant_id.astype("int").\
                       astype('str').unique().tolist())
