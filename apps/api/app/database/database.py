import numpy
import pandas as pd

from app.config import resolve_legacy_data_path

from .sql.sqlite import SQLDatabase
from .vector.chromadb import VectorDatabase

FILTER_COLUMNS = (
    "gender",
    "masterCategory",
    "subCategory",
    "articleType",
    "baseColour",
    "season",
    "usage",
)


class DatabaseService:
    def __init__(self):
        self.vector_db = VectorDatabase()
        self.sql_db = SQLDatabase()

    def reset_vector_db(self):
        self.vector_db.delete_collection()
        self.vector_db.create_collection()

    def load_image_uris_vector_db(self, ids: list[str], uris: list[str]):
        self.vector_db.get_collection().add(ids=ids, uris=uris)

    def load_dataframe_sql_db(self, dataframe: pd.DataFrame):
        self.sql_db.load_dataframe(dataframe)

    def query_vector_db_text(self, text: str):
        return self.vector_db.query_text(text)

    def query_vector_db_image(self, image: numpy.ndarray):
        return self.vector_db.query_image(image)

    def query_vector_db_embeddings(self, embeddings: numpy.ndarray):
        return self.vector_db.query_embeddings(embeddings)

    def get_product_ids_metadata(self) -> tuple[list[str], list[str]]:
        results = self.sql_db.execute_query("SELECT id, metadata FROM products")
        if not results:
            return [], []
        ids, metadata = zip(*results, strict=True)
        return list(ids), list(metadata)

    def product_exists(self, product_id: str) -> bool:
        results = self.sql_db.execute_query(
            "SELECT 1 FROM products WHERE id = ? LIMIT 1", (product_id,)
        )
        return bool(results)

    def get_metadata_from_product_ids(self, product_ids: list[str]) -> dict[str, str]:
        if not product_ids:
            return {}
        placeholders = ",".join("?" for _ in product_ids)
        query = f"SELECT image_uri, metadata FROM products WHERE id IN ({placeholders})"
        results = self.sql_db.execute_query(query, tuple(product_ids))
        return {str(resolve_legacy_data_path(uri)): metadata for uri, metadata in results}

    def get_article_types(self) -> list[str]:
        results = self.sql_db.execute_query("SELECT DISTINCT articleType FROM products")
        return [row[0] for row in results]

    def get_product_terms(self) -> list[str]:
        columns = [
            "gender",
            "masterCategory",
            "subCategory",
            "articleType",
            "baseColour",
            "season",
            "usage",
        ]
        query = " UNION ALL ".join(
            f"SELECT DISTINCT {col} FROM products" for col in columns
        )
        labels = [row[0] for row in self.sql_db.execute_query(query)]
        return [label for label in labels if label is not None]

    def get_product_uris_by_article_type(self, article_type: str) -> list[str]:
        if article_type:
            query = (
                "SELECT high_resolution_image_uri FROM products WHERE articleType = ?"
            )
        else:
            query = "SELECT high_resolution_image_uri FROM products"
        results = self.sql_db.execute_query(
            query, (article_type,) if article_type else ()
        )
        return [row[0] for row in results]

    def get_filter_options(self) -> dict[str, list[str]]:
        return {
            column: [
                row[0]
                for row in self.sql_db.execute_query(
                    f"SELECT DISTINCT {column} FROM products "
                    f"WHERE {column} IS NOT NULL ORDER BY {column}"
                )
            ]
            for column in FILTER_COLUMNS
        }

    def list_products(
        self, filters: dict[str, str], limit: int, offset: int
    ) -> tuple[list[tuple], int]:
        active_columns = [column for column in FILTER_COLUMNS if filters.get(column)]
        where_clause = " AND ".join(f"{column} = ?" for column in active_columns) or "1=1"
        params = tuple(filters[column] for column in active_columns)

        total = self.sql_db.execute_query(
            f"SELECT COUNT(*) FROM products WHERE {where_clause}", params
        )[0][0]
        rows = self.sql_db.execute_query(
            "SELECT id, productDisplayName, gender, masterCategory, subCategory, "
            f"articleType, baseColour, season, usage FROM products WHERE {where_clause} "
            "ORDER BY id LIMIT ? OFFSET ?",
            (*params, limit, offset),
        )
        return rows, total
