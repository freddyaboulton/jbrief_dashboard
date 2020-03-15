import os

_db_user = os.environ['db_user']
_db_password = os.environ['db_password']
_db_uri = os.environ['db_uri']

DB_CONNECTION = f"postgresql+psycopg2://{_db_user}:{_db_password}@{_db_uri}"
DATE_FORMAT = "%Y-%m-%d"