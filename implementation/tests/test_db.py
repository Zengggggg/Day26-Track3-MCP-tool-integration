from pathlib import Path

import pytest

from implementation.db import PostgresAdapter, SQLiteAdapter, ValidationError, create_adapter
from implementation.init_db import create_database


@pytest.fixture()
def adapter(tmp_path: Path) -> SQLiteAdapter:
    db_path = create_database(tmp_path / "lab.db")
    return SQLiteAdapter(db_path)


def test_search_filters_ordering_and_pagination(adapter: SQLiteAdapter):
    result = adapter.search(
        "students",
        filters=[{"column": "cohort", "op": "=", "value": "A1"}],
        columns=["name", "score"],
        order_by="score",
        descending=True,
        limit=2,
    )

    assert result["count"] == 2
    assert result["rows"][0]["name"] == "Emma Vo"
    assert list(result["rows"][0].keys()) == ["name", "score"]
    assert result["pagination"] == {
        "limit": 2,
        "offset": 0,
        "returned": 2,
        "has_more": True,
        "next_offset": 2,
    }
    assert result["annotations"]["backend"] == "SQLiteAdapter"


def test_insert_returns_generated_id(adapter: SQLiteAdapter):
    result = adapter.insert(
        "students",
        {
            "name": "Minh Ho",
            "cohort": "C3",
            "email": "minh.ho@example.edu",
            "score": 81.0,
        },
    )

    assert result["inserted"]["id"] > 0
    assert result["inserted"]["email"] == "minh.ho@example.edu"
    assert result["annotations"]["primary_key"] == "id"


def test_aggregate_average_by_group(adapter: SQLiteAdapter):
    result = adapter.aggregate(
        "students",
        metric="avg",
        column="score",
        group_by="cohort",
    )

    rows = {row["group_value"]: row["value"] for row in result["rows"]}
    assert rows["A1"] == pytest.approx((91.5 + 84.0 + 95.0) / 3)
    assert rows["B2"] == pytest.approx((77.5 + 88.0) / 2)
    assert result["annotations"]["grouped"] is True


def test_unknown_table_is_rejected(adapter: SQLiteAdapter):
    with pytest.raises(ValidationError, match="unknown table"):
        adapter.search("missing_table")


def test_unknown_column_is_rejected(adapter: SQLiteAdapter):
    with pytest.raises(ValidationError, match="unknown column"):
        adapter.search("students", columns=["name", "password"])


def test_unsupported_operator_is_rejected(adapter: SQLiteAdapter):
    with pytest.raises(ValidationError, match="unsupported filter operator"):
        adapter.search(
            "students",
            filters=[{"column": "name", "op": "regexp", "value": "A.*"}],
        )


def test_bad_aggregate_is_rejected(adapter: SQLiteAdapter):
    with pytest.raises(ValidationError, match="requires a column"):
        adapter.aggregate("students", metric="avg")


def test_empty_insert_is_rejected(adapter: SQLiteAdapter):
    with pytest.raises(ValidationError, match="cannot be empty"):
        adapter.insert("students", {})


def test_adapter_factory_defaults_to_sqlite(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db_path = tmp_path / "lab.db"

    result = create_adapter(db_path)

    assert isinstance(result, SQLiteAdapter)


def test_adapter_factory_selects_postgres(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/lab")

    result = create_adapter(tmp_path / "lab.db")

    assert isinstance(result, PostgresAdapter)
    assert result.database_url == "postgresql://user:pass@localhost/lab"
