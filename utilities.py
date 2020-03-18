from typing import List
import pandas as pd


def get_unique_contestant_ids(df: pd.DataFrame) -> List[str]:

    return ",".join(df.contestant_id.astype("int").\
                       astype('str').unique().tolist())