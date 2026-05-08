import os
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()


def get_engine() -> Engine:
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "skyw3lker")
    host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "olist_mid_presentation")

    connection_string = (
        f"mysql+mysqlconnector://{user}:{password}@{host}/{db_name}"
    )
    return create_engine(connection_string, pool_pre_ping=True)


engine = get_engine()


def run_query(query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})