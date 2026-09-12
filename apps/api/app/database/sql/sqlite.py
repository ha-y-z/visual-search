import contextlib
import sqlite3

import pandas as pd

from app.config import settings

_INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS idx_products_id ON products(id)",
    "CREATE INDEX IF NOT EXISTS idx_products_article_type ON products(articleType)",
)


class SQLDatabase:
    def __init__(self) -> None:
        self._ensure_indexes()

    def get_conn(self) -> sqlite3.Connection:
        # execute_query is used exclusively for SELECTs in this codebase (load_dataframe
        # and the index migration use get_writable_conn instead), so opening read paths
        # in SQLite's URI read-only mode means a stray write can never slip through here.
        return sqlite3.connect(f"file:{settings.SQLITE_PATH}?mode=ro", uri=True)

    def get_writable_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(settings.SQLITE_PATH)

    def get_cursor(self, conn: sqlite3.Connection) -> sqlite3.Cursor:
        return conn.cursor()

    def execute_query(self, query: str, params: tuple = ()) -> list:
        # contextlib.closing, not `with conn:` -- sqlite3.Connection's own context
        # manager only commits/rolls back a transaction on exit, it never closes
        # the connection, so a raised exception here would otherwise leak it.
        with contextlib.closing(self.get_conn()) as conn:
            cursor = self.get_cursor(conn)
            cursor.execute(query, params)
            return cursor.fetchall()

    def load_dataframe(self, dataframe: pd.DataFrame) -> None:
        with contextlib.closing(self.get_writable_conn()) as conn:
            dataframe.to_sql("products", conn, if_exists="replace", index=False)

    def _ensure_indexes(self) -> None:
        # `, conn` re-enters conn's own context manager for the commit; closing()
        # around it is still what actually closes the connection afterward.
        with contextlib.closing(self.get_writable_conn()) as conn, conn:
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='products'"
            ).fetchone()
            if table_exists:
                for statement in _INDEX_STATEMENTS:
                    conn.execute(statement)
