import sqlite3

from app.database.database import DatabaseService
from app.database.sql.sqlite import SQLDatabase


def _make_service() -> DatabaseService:
    # Bypass __init__ (which builds a VectorDatabase and loads the CLIP model) --
    # get_product_ids_metadata / get_metadata_from_product_ids only touch sql_db.
    service = DatabaseService.__new__(DatabaseService)
    service.sql_db = SQLDatabase()
    return service


def test_get_product_ids_metadata_returns_rows(sqlite_products_db):
    service = _make_service()
    ids, metadata = service.get_product_ids_metadata()
    assert sorted(ids) == ["1", "2"]
    assert len(metadata) == 2


def test_get_product_ids_metadata_empty_table_does_not_raise(isolated_data_dir):
    from app.config import settings

    settings.SQLITE_PATH.parent.mkdir(parents=True)
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.execute("CREATE TABLE products (id TEXT, metadata TEXT, articleType TEXT)")
    conn.commit()
    conn.close()

    service = _make_service()
    ids, metadata = service.get_product_ids_metadata()

    assert ids == []
    assert metadata == []


def test_get_metadata_from_product_ids_empty_list_returns_empty_dict(sqlite_products_db):
    service = _make_service()
    assert service.get_metadata_from_product_ids([]) == {}


def test_get_metadata_from_product_ids_builds_correct_in_clause(sqlite_products_db):
    service = _make_service()
    result = service.get_metadata_from_product_ids(["1", "2"])
    assert len(result) == 2
    assert "red shirt" in result.values()
    assert "blue jeans" in result.values()


def test_get_metadata_from_product_ids_unknown_id_is_absent(sqlite_products_db):
    service = _make_service()
    result = service.get_metadata_from_product_ids(["does-not-exist"])
    assert result == {}


def test_product_exists(sqlite_products_db):
    service = _make_service()
    assert service.product_exists("1") is True
    assert service.product_exists("missing") is False


def test_index_migration_creates_indexes_idempotently(sqlite_products_db):
    SQLDatabase()
    SQLDatabase()  # second construction must not fail (IF NOT EXISTS)

    conn = sqlite3.connect(sqlite_products_db)
    names = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    }
    conn.close()
    assert "idx_products_id" in names
    assert "idx_products_article_type" in names


def test_index_migration_uses_index_for_id_lookup(sqlite_products_db):
    SQLDatabase()
    conn = sqlite3.connect(sqlite_products_db)
    plan = conn.execute("EXPLAIN QUERY PLAN SELECT * FROM products WHERE id IN ('1','2')").fetchall()
    conn.close()
    plan_text = " ".join(str(row) for row in plan)
    assert "SEARCH" in plan_text
    assert "SCAN products" not in plan_text
