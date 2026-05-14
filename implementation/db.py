from __future__ import annotations

import os
import re
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


class ValidationError(ValueError):
    """Raised when a request cannot be safely executed."""


Filter = Dict[str, Any]


class BaseDatabaseAdapter(ABC):
    """Shared MCP database surface for SQLite and PostgreSQL backends."""

    SUPPORTED_OPERATORS = {
        "=": "=",
        "==": "=",
        "eq": "=",
        "!=": "!=",
        "<>": "!=",
        "ne": "!=",
        ">": ">",
        "gt": ">",
        ">=": ">=",
        "gte": ">=",
        "<": "<",
        "lt": "<",
        "<=": "<=",
        "lte": "<=",
        "like": "LIKE",
        "in": "IN",
    }
    SUPPORTED_METRICS = {"count", "avg", "sum", "min", "max"}
    IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    PARAM_STYLE = "?"

    @abstractmethod
    def list_tables(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def _table_columns(self, table: str) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def _primary_key_column(self, table: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def _execute_rows(self, sql: str, params: Sequence[Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def _execute_insert(
        self, sql: str, params: Sequence[Any], table: str, pk_column: Optional[str]
    ) -> Optional[Any]:
        raise NotImplementedError

    @property
    @abstractmethod
    def database_label(self) -> str:
        raise NotImplementedError

    def get_database_schema(self) -> Dict[str, Any]:
        return {
            "database": self.database_label,
            "backend": self.__class__.__name__,
            "tables": {
                table: {"columns": self.get_table_schema(table)}
                for table in self.list_tables()
            },
        }

    def search(
        self,
        table: str,
        columns: Optional[Sequence[str]] = None,
        filters: Optional[Sequence[Filter]] = None,
        limit: int = 20,
        offset: int = 0,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> Dict[str, Any]:
        available_columns = self._validate_table(table)
        selected_columns = self._validate_columns(columns, available_columns)
        limit, offset = self._validate_pagination(limit, offset)

        where_sql, params = self._build_where(filters, available_columns)
        order_sql = ""
        if order_by:
            self._validate_column(order_by, available_columns)
            order_sql = ' ORDER BY "{}" {}'.format(
                order_by, "DESC" if descending else "ASC"
            )

        column_sql = ", ".join('"{}"'.format(column) for column in selected_columns)
        fetch_limit = limit + 1
        sql = 'SELECT {} FROM "{}"{}{} LIMIT {} OFFSET {}'.format(
            column_sql,
            table,
            where_sql,
            order_sql,
            self.placeholder(),
            self.placeholder(),
        )
        query_params = list(params) + [fetch_limit, offset]
        fetched_rows = self._execute_rows(sql, query_params)
        rows = fetched_rows[:limit]
        has_more = len(fetched_rows) > limit

        return {
            "table": table,
            "columns": selected_columns,
            "filters": list(filters or []),
            "limit": limit,
            "offset": offset,
            "count": len(rows),
            "rows": rows,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(rows),
                "has_more": has_more,
                "next_offset": offset + limit if has_more else None,
            },
            "annotations": {
                "backend": self.__class__.__name__,
                "selected_columns": len(selected_columns),
                "filter_count": len(filters or []),
                "ordered_by": order_by,
                "order_direction": "desc" if descending else "asc",
            },
        }

    def insert(self, table: str, values: Dict[str, Any]) -> Dict[str, Any]:
        available_columns = self._validate_table(table)
        if not values:
            raise ValidationError("insert values cannot be empty")
        if not isinstance(values, dict):
            raise ValidationError("insert values must be an object")

        for column in values:
            self._validate_column(column, available_columns)

        columns = list(values.keys())
        placeholders = ", ".join(self.placeholder() for _ in columns)
        column_sql = ", ".join('"{}"'.format(column) for column in columns)
        pk_column = self._primary_key_column(table)
        returning_sql = ' RETURNING "{}"'.format(pk_column) if pk_column else ""
        sql = 'INSERT INTO "{}" ({}) VALUES ({}){}'.format(
            table, column_sql, placeholders, returning_sql
        )
        inserted_id = self._execute_insert(
            sql, [values[column] for column in columns], table, pk_column
        )

        inserted = dict(values)
        if pk_column and pk_column not in inserted and inserted_id is not None:
            inserted[pk_column] = inserted_id

        return {
            "table": table,
            "inserted": inserted,
            "annotations": {
                "backend": self.__class__.__name__,
                "inserted_columns": columns,
                "primary_key": pk_column,
            },
        }

    def aggregate(
        self,
        table: str,
        metric: str,
        column: Optional[str] = None,
        filters: Optional[Sequence[Filter]] = None,
        group_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        available_columns = self._validate_table(table)
        normalized_metric = str(metric).lower()
        if normalized_metric not in self.SUPPORTED_METRICS:
            raise ValidationError(
                "unsupported aggregate metric '{}'; supported metrics: {}".format(
                    metric, ", ".join(sorted(self.SUPPORTED_METRICS))
                )
            )

        if normalized_metric == "count":
            aggregate_expr = "COUNT(*)"
        else:
            if not column:
                raise ValidationError("{} requires a column".format(normalized_metric))
            self._validate_column(column, available_columns)
            aggregate_expr = '{}("{}")'.format(normalized_metric.upper(), column)

        select_parts = []
        group_sql = ""
        if group_by:
            self._validate_column(group_by, available_columns)
            select_parts.append('"{}" AS group_value'.format(group_by))
            group_sql = ' GROUP BY "{}" ORDER BY "{}" ASC'.format(group_by, group_by)

        select_parts.append("{} AS value".format(aggregate_expr))
        where_sql, params = self._build_where(filters, available_columns)
        sql = 'SELECT {} FROM "{}"{}{}'.format(
            ", ".join(select_parts), table, where_sql, group_sql
        )

        rows = self._execute_rows(sql, params)
        return {
            "table": table,
            "metric": normalized_metric,
            "column": column,
            "group_by": group_by,
            "filters": list(filters or []),
            "rows": rows,
            "annotations": {
                "backend": self.__class__.__name__,
                "grouped": bool(group_by),
                "filter_count": len(filters or []),
            },
        }

    def placeholder(self) -> str:
        return self.PARAM_STYLE

    def _validate_table(self, table: str) -> List[str]:
        self._validate_identifier(table, "table")
        tables = self.list_tables()
        if table not in tables:
            raise ValidationError(
                "unknown table '{}'; available tables: {}".format(
                    table, ", ".join(tables)
                )
            )
        return self._table_columns(table)

    def _validate_columns(
        self, columns: Optional[Sequence[str]], available_columns: Sequence[str]
    ) -> List[str]:
        if not columns:
            return list(available_columns)
        selected = []
        for column in columns:
            self._validate_column(column, available_columns)
            selected.append(column)
        return selected

    def _validate_column(self, column: str, available_columns: Sequence[str]) -> None:
        self._validate_identifier(column, "column")
        if column not in available_columns:
            raise ValidationError(
                "unknown column '{}'; available columns: {}".format(
                    column, ", ".join(available_columns)
                )
            )

    def _validate_identifier(self, identifier: str, kind: str) -> None:
        if not isinstance(identifier, str) or not self.IDENTIFIER_RE.match(identifier):
            raise ValidationError("invalid {} identifier '{}'".format(kind, identifier))

    def _validate_pagination(self, limit: int, offset: int) -> Tuple[int, int]:
        try:
            limit = int(limit)
            offset = int(offset)
        except (TypeError, ValueError):
            raise ValidationError("limit and offset must be integers")
        if limit < 1 or limit > 100:
            raise ValidationError("limit must be between 1 and 100")
        if offset < 0:
            raise ValidationError("offset must be greater than or equal to 0")
        return limit, offset

    def _build_where(
        self, filters: Optional[Sequence[Filter]], available_columns: Sequence[str]
    ) -> Tuple[str, List[Any]]:
        if not filters:
            return "", []
        if not isinstance(filters, list):
            raise ValidationError("filters must be a list of filter objects")

        clauses = []
        params: List[Any] = []
        for item in filters:
            if not isinstance(item, dict):
                raise ValidationError("each filter must be an object")
            column = item.get("column")
            op = str(item.get("op", "=")).lower()
            value = item.get("value")
            self._validate_column(column, available_columns)
            if op not in self.SUPPORTED_OPERATORS:
                raise ValidationError(
                    "unsupported filter operator '{}'; supported operators: {}".format(
                        op, ", ".join(sorted(self.SUPPORTED_OPERATORS))
                    )
                )

            sql_op = self.SUPPORTED_OPERATORS[op]
            if sql_op == "IN":
                if not isinstance(value, list) or not value:
                    raise ValidationError("IN filters require a non-empty list value")
                placeholders = ", ".join(self.placeholder() for _ in value)
                clauses.append('"{}" IN ({})'.format(column, placeholders))
                params.extend(value)
            else:
                clauses.append('"{}" {} {}'.format(column, sql_op, self.placeholder()))
                params.append(value)

        return " WHERE " + " AND ".join(clauses), params


class SQLiteAdapter(BaseDatabaseAdapter):
    """SQLite implementation of the shared lab database adapter."""

    PARAM_STYLE = "?"

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    @property
    def database_label(self) -> str:
        return str(self.db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def list_tables(self) -> List[str]:
        rows = self._execute_rows(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """,
            [],
        )
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        self._validate_table(table)
        rows = self._execute_rows('PRAGMA table_info("{}")'.format(table), [])
        return [
            {
                "name": row["name"],
                "type": row["type"],
                "nullable": not bool(row["notnull"]),
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            }
            for row in rows
        ]

    def _execute_rows(self, sql: str, params: Sequence[Any]) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, list(params)).fetchall()]

    def _execute_insert(
        self, sql: str, params: Sequence[Any], table: str, pk_column: Optional[str]
    ) -> Optional[Any]:
        with self.connect() as conn:
            cursor = conn.execute(sql, list(params))
            row = cursor.fetchone() if pk_column else None
            conn.commit()
            if row is not None:
                return row[0]
            return cursor.lastrowid

    def _table_columns(self, table: str) -> List[str]:
        rows = self._execute_rows('PRAGMA table_info("{}")'.format(table), [])
        return [row["name"] for row in rows]

    def _primary_key_column(self, table: str) -> Optional[str]:
        for column in self.get_table_schema(table):
            if column["primary_key"]:
                return column["name"]
        return None


class PostgresAdapter(BaseDatabaseAdapter):
    """PostgreSQL implementation selected with DATABASE_URL."""

    PARAM_STYLE = "%s"

    def __init__(self, database_url: str, schema: str = "public"):
        self.database_url = database_url
        self.schema = schema

    @property
    def database_label(self) -> str:
        return self.database_url

    def connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as error:
            raise RuntimeError(
                "PostgreSQL support requires psycopg. Install requirements.txt first."
            ) from error
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def list_tables(self) -> List[str]:
        rows = self._execute_rows(
            """
            SELECT table_name AS name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            [self.schema],
        )
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        self._validate_table(table)
        columns = self._execute_rows(
            """
            SELECT
                c.column_name AS name,
                c.data_type AS type,
                c.is_nullable AS nullable,
                c.column_default AS default,
                CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN true ELSE false END
                    AS primary_key
            FROM information_schema.columns c
            LEFT JOIN information_schema.key_column_usage kcu
              ON c.table_schema = kcu.table_schema
             AND c.table_name = kcu.table_name
             AND c.column_name = kcu.column_name
            LEFT JOIN information_schema.table_constraints tc
              ON kcu.constraint_schema = tc.constraint_schema
             AND kcu.constraint_name = tc.constraint_name
             AND tc.constraint_type = 'PRIMARY KEY'
            WHERE c.table_schema = %s
              AND c.table_name = %s
            ORDER BY c.ordinal_position
            """,
            [self.schema, table],
        )
        return [
            {
                "name": row["name"],
                "type": row["type"],
                "nullable": row["nullable"] == "YES",
                "default": row["default"],
                "primary_key": bool(row["primary_key"]),
            }
            for row in columns
        ]

    def _execute_rows(self, sql: str, params: Sequence[Any]) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, list(params))
                return [dict(row) for row in cur.fetchall()]

    def _execute_insert(
        self, sql: str, params: Sequence[Any], table: str, pk_column: Optional[str]
    ) -> Optional[Any]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, list(params))
                row = cur.fetchone() if pk_column else None
                conn.commit()
                return row[pk_column] if row and pk_column else None

    def _table_columns(self, table: str) -> List[str]:
        rows = self._execute_rows(
            """
            SELECT column_name AS name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            [self.schema, table],
        )
        return [row["name"] for row in rows]

    def _primary_key_column(self, table: str) -> Optional[str]:
        for column in self.get_table_schema(table):
            if column["primary_key"]:
                return column["name"]
        return None


def create_adapter(
    default_sqlite_path: Path,
    database_url: Optional[str] = None,
) -> BaseDatabaseAdapter:
    """Create the configured database adapter without changing the MCP surface."""
    url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
    if url.startswith(("postgresql://", "postgres://")):
        return PostgresAdapter(url, schema=os.getenv("POSTGRES_SCHEMA", "public"))
    return SQLiteAdapter(default_sqlite_path)
