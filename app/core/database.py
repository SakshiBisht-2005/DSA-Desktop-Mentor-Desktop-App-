from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.core.config import DB_PATH


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    selected_language TEXT NOT NULL DEFAULT 'Python',
                    theme TEXT NOT NULL DEFAULT 'dark',
                    reminders_enabled INTEGER NOT NULL DEFAULT 1,
                    onboarding_seen INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                );

                CREATE TABLE IF NOT EXISTS topic_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic_slug TEXT NOT NULL,
                    topic_index INTEGER NOT NULL,
                    unlocked INTEGER NOT NULL DEFAULT 0,
                    completed INTEGER NOT NULL DEFAULT 0,
                    needs_revision INTEGER NOT NULL DEFAULT 0,
                    started_on TEXT,
                    completed_on TEXT,
                    last_studied_on TEXT,
                    UNIQUE(user_id, topic_slug),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic_slug TEXT NOT NULL,
                    studied_on TEXT NOT NULL,
                    session_date TEXT NOT NULL,
                    action TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    coverage_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL,
                    passed INTEGER NOT NULL DEFAULT 0,
                    topics_json TEXT NOT NULL,
                    study_dates_json TEXT NOT NULL,
                    questions_json TEXT NOT NULL,
                    answers_json TEXT,
                    feedback_json TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, coverage_key),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topic_slug TEXT NOT NULL,
                    content TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, topic_slug),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS practice_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    problem_id TEXT NOT NULL,
                    topic_slug TEXT NOT NULL,
                    code TEXT NOT NULL DEFAULT '',
                    feedback TEXT NOT NULL DEFAULT '',
                    score REAL NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    viewed_solution INTEGER NOT NULL DEFAULT 0,
                    last_submitted_at TEXT,
                    UNIQUE(user_id, problem_id),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    problem_id TEXT NOT NULL,
                    topic_slug TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, problem_id),
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_topic_progress_user_index
                    ON topic_progress(user_id, topic_index);
                CREATE INDEX IF NOT EXISTS idx_topic_progress_user_completed
                    ON topic_progress(user_id, completed, needs_revision);
                CREATE INDEX IF NOT EXISTS idx_study_sessions_user_date
                    ON study_sessions(user_id, session_date);
                CREATE INDEX IF NOT EXISTS idx_tests_user_status
                    ON tests(user_id, status, id DESC);
                CREATE INDEX IF NOT EXISTS idx_practice_attempts_user_topic
                    ON practice_attempts(user_id, topic_slug, last_submitted_at DESC);
                CREATE INDEX IF NOT EXISTS idx_bookmarks_user_topic
                    ON bookmarks(user_id, topic_slug, created_at DESC);
                """
            )
            self._run_migrations(connection)

    def _run_migrations(self, connection: sqlite3.Connection) -> None:
        self._ensure_column(
            connection,
            "users",
            "onboarding_seen",
            "INTEGER NOT NULL DEFAULT 0",
        )

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_definition: str,
    ) -> None:
        columns = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name not in columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            )

    @contextmanager
    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
