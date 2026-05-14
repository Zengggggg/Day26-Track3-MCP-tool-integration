from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = Path(__file__).with_name("lab.db")

SCHEMA_SQL = """
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    score REAL NOT NULL CHECK(score >= 0 AND score <= 100)
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK(credits > 0)
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    grade REAL NOT NULL CHECK(grade >= 0 AND grade <= 100),
    status TEXT NOT NULL DEFAULT 'active',
    UNIQUE(student_id, course_id)
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, email, score) VALUES
    ('An Nguyen', 'A1', 'an.nguyen@example.edu', 91.5),
    ('Binh Tran', 'A1', 'binh.tran@example.edu', 84.0),
    ('Chi Le', 'B2', 'chi.le@example.edu', 77.5),
    ('Dung Pham', 'B2', 'dung.pham@example.edu', 88.0),
    ('Emma Vo', 'A1', 'emma.vo@example.edu', 95.0);

INSERT INTO courses (code, title, credits) VALUES
    ('AI101', 'Introduction to AI', 3),
    ('DB201', 'Database Systems', 4),
    ('MCP301', 'MCP Tool Integration', 2);

INSERT INTO enrollments (student_id, course_id, grade, status) VALUES
    (1, 1, 92.0, 'active'),
    (1, 3, 94.0, 'active'),
    (2, 1, 86.0, 'active'),
    (2, 2, 82.0, 'active'),
    (3, 2, 78.0, 'active'),
    (4, 3, 89.0, 'active'),
    (5, 1, 96.0, 'active'),
    (5, 3, 97.0, 'active');
"""


def create_database(db_path: Optional[Path] = None) -> Path:
    """Create a reproducible SQLite database and return its path."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.executescript(SEED_SQL)
        conn.commit()
    return path


if __name__ == "__main__":
    print(create_database())

