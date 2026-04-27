from __future__ import annotations

import json
from collections.abc import Iterable

from app.core.database import DatabaseManager


class LearningRepository:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def initialize_progress(self, user_id: int, topic_order: list[str]) -> None:
        with self.database.connect() as connection:
            for index, topic_slug in enumerate(topic_order):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO topic_progress (
                        user_id, topic_slug, topic_index, unlocked
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, topic_slug, index, int(index == 0)),
                )

    def get_progress_rows(self, user_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM topic_progress
                WHERE user_id = ?
                ORDER BY topic_index
                """,
                (user_id,),
            ).fetchall()

    def get_progress_row(self, user_id: int, topic_slug: str):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM topic_progress
                WHERE user_id = ? AND topic_slug = ?
                """,
                (user_id, topic_slug),
            ).fetchone()

    def update_topic_flags(
        self,
        user_id: int,
        topic_slug: str,
        *,
        unlocked: bool | None = None,
        completed: bool | None = None,
        needs_revision: bool | None = None,
        started_on: str | None = None,
        completed_on: str | None = None,
        last_studied_on: str | None = None,
    ) -> None:
        fields = []
        values = []
        if unlocked is not None:
            fields.append("unlocked = ?")
            values.append(int(unlocked))
        if completed is not None:
            fields.append("completed = ?")
            values.append(int(completed))
        if needs_revision is not None:
            fields.append("needs_revision = ?")
            values.append(int(needs_revision))
        if started_on is not None:
            fields.append("started_on = COALESCE(started_on, ?)")
            values.append(started_on)
        if completed_on is not None:
            fields.append("completed_on = ?")
            values.append(completed_on)
        if last_studied_on is not None:
            fields.append("last_studied_on = ?")
            values.append(last_studied_on)
        if not fields:
            return
        values.extend((user_id, topic_slug))
        with self.database.connect() as connection:
            connection.execute(
                f"""
                UPDATE topic_progress
                SET {', '.join(fields)}
                WHERE user_id = ? AND topic_slug = ?
                """,
                tuple(values),
            )

    def record_study_session(
        self,
        user_id: int,
        topic_slug: str,
        studied_on: str,
        session_date: str,
        action: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO study_sessions (user_id, topic_slug, studied_on, session_date, action)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, topic_slug, studied_on, session_date, action),
            )

    def get_distinct_study_dates_after(self, user_id: int, anchor_date: str | None):
        query = """
            SELECT DISTINCT session_date
            FROM study_sessions
            WHERE user_id = ?
        """
        params: list[object] = [user_id]
        if anchor_date:
            query += " AND session_date > ?"
            params.append(anchor_date)
        query += " ORDER BY session_date"
        with self.database.connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [row["session_date"] for row in rows]

    def get_topics_for_dates(self, user_id: int, session_dates: Iterable[str]) -> list[str]:
        dates = list(session_dates)
        if not dates:
            return []
        placeholders = ", ".join("?" for _ in dates)
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT topic_slug, MIN(id) AS first_seen
                FROM study_sessions
                WHERE user_id = ? AND session_date IN ({placeholders})
                GROUP BY topic_slug
                ORDER BY first_seen
                """,
                (user_id, *dates),
            ).fetchall()
        return [row["topic_slug"] for row in rows]

    def create_test(
        self,
        user_id: int,
        coverage_key: str,
        status: str,
        topics: list[str],
        study_dates: list[str],
        questions: list[dict],
        created_at: str,
    ) -> int:
        payload = (
            user_id,
            coverage_key,
            status,
            json.dumps(topics),
            json.dumps(study_dates),
            json.dumps(questions),
            created_at,
            created_at,
        )
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO tests (
                    user_id, coverage_key, status, topics_json, study_dates_json,
                    questions_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            return int(cursor.lastrowid)

    def get_active_test(self, user_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM tests
                WHERE user_id = ? AND status IN ('due', 'revision_required')
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

    def get_test_by_id(self, user_id: int, test_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                "SELECT * FROM tests WHERE user_id = ? AND id = ?",
                (user_id, test_id),
            ).fetchone()

    def get_latest_passed_test(self, user_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM tests
                WHERE user_id = ? AND status = 'passed'
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

    def get_test_history(self, user_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM tests
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,),
            ).fetchall()

    def update_test(
        self,
        test_id: int,
        *,
        status: str,
        score: float,
        passed: bool,
        answers: list[dict],
        feedback: list[dict],
        attempts: int,
        updated_at: str,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE tests
                SET status = ?, score = ?, passed = ?, answers_json = ?, feedback_json = ?,
                    attempts = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    score,
                    int(passed),
                    json.dumps(answers),
                    json.dumps(feedback),
                    attempts,
                    updated_at,
                    test_id,
                ),
            )

    def get_note(self, user_id: int, topic_slug: str) -> str:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT content FROM notes
                WHERE user_id = ? AND topic_slug = ?
                """,
                (user_id, topic_slug),
            ).fetchone()
        return row["content"] if row else ""

    def save_note(self, user_id: int, topic_slug: str, content: str, updated_at: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO notes (user_id, topic_slug, content, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, topic_slug) DO UPDATE SET
                    content = excluded.content,
                    updated_at = excluded.updated_at
                """,
                (user_id, topic_slug, content, updated_at),
            )

    def get_practice_attempt(self, user_id: int, problem_id: str):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM practice_attempts
                WHERE user_id = ? AND problem_id = ?
                """,
                (user_id, problem_id),
            ).fetchone()

    def save_practice_attempt(
        self,
        user_id: int,
        topic_slug: str,
        problem_id: str,
        code: str,
        feedback: str,
        score: float,
        viewed_solution: bool,
        last_submitted_at: str,
    ) -> None:
        with self.database.connect() as connection:
            current = connection.execute(
                """
                SELECT attempts FROM practice_attempts
                WHERE user_id = ? AND problem_id = ?
                """,
                (user_id, problem_id),
            ).fetchone()
            attempts = (current["attempts"] if current else 0) + 1
            connection.execute(
                """
                INSERT INTO practice_attempts (
                    user_id, problem_id, topic_slug, code, feedback, score,
                    attempts, viewed_solution, last_submitted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, problem_id) DO UPDATE SET
                    code = excluded.code,
                    feedback = excluded.feedback,
                    score = excluded.score,
                    attempts = excluded.attempts,
                    viewed_solution = excluded.viewed_solution,
                    last_submitted_at = excluded.last_submitted_at
                """,
                (
                    user_id,
                    problem_id,
                    topic_slug,
                    code,
                    feedback,
                    score,
                    attempts,
                    int(viewed_solution),
                    last_submitted_at,
                ),
            )

    def save_practice_draft(
        self,
        user_id: int,
        topic_slug: str,
        problem_id: str,
        code: str,
        last_updated_at: str,
    ) -> None:
        with self.database.connect() as connection:
            current = connection.execute(
                """
                SELECT * FROM practice_attempts
                WHERE user_id = ? AND problem_id = ?
                """,
                (user_id, problem_id),
            ).fetchone()
            if current:
                connection.execute(
                    """
                    UPDATE practice_attempts
                    SET code = ?, last_submitted_at = ?
                    WHERE user_id = ? AND problem_id = ?
                    """,
                    (code, last_updated_at, user_id, problem_id),
                )
                return
            connection.execute(
                """
                INSERT INTO practice_attempts (
                    user_id, problem_id, topic_slug, code, feedback, score,
                    attempts, viewed_solution, last_submitted_at
                )
                VALUES (?, ?, ?, ?, '', 0, 0, 0, ?)
                """,
                (user_id, problem_id, topic_slug, code, last_updated_at),
            )

    def mark_solution_viewed(self, user_id: int, topic_slug: str, problem_id: str, timestamp: str) -> None:
        with self.database.connect() as connection:
            current = connection.execute(
                """
                SELECT * FROM practice_attempts
                WHERE user_id = ? AND problem_id = ?
                """,
                (user_id, problem_id),
            ).fetchone()
            attempts = current["attempts"] if current else 0
            code = current["code"] if current else ""
            feedback = current["feedback"] if current else ""
            score = current["score"] if current else 0
            connection.execute(
                """
                INSERT INTO practice_attempts (
                    user_id, problem_id, topic_slug, code, feedback, score,
                    attempts, viewed_solution, last_submitted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(user_id, problem_id) DO UPDATE SET
                    viewed_solution = 1,
                    last_submitted_at = excluded.last_submitted_at
                """,
                (
                    user_id,
                    problem_id,
                    topic_slug,
                    code,
                    feedback,
                    score,
                    attempts,
                    timestamp,
                ),
            )

    def get_practice_rows(self, user_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM practice_attempts
                WHERE user_id = ?
                ORDER BY last_submitted_at DESC
                """,
                (user_id,),
            ).fetchall()

    def get_bookmarks(self, user_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """
                SELECT * FROM bookmarks
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()

    def is_bookmarked(self, user_id: int, problem_id: str) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM bookmarks
                WHERE user_id = ? AND problem_id = ?
                """,
                (user_id, problem_id),
            ).fetchone()
        return row is not None

    def toggle_bookmark(self, user_id: int, topic_slug: str, problem_id: str, timestamp: str) -> bool:
        with self.database.connect() as connection:
            existing = connection.execute(
                """
                SELECT id FROM bookmarks
                WHERE user_id = ? AND problem_id = ?
                """,
                (user_id, problem_id),
            ).fetchone()
            if existing:
                connection.execute(
                    "DELETE FROM bookmarks WHERE id = ?",
                    (existing["id"],),
                )
                return False
            connection.execute(
                """
                INSERT INTO bookmarks (user_id, problem_id, topic_slug, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, problem_id, topic_slug, timestamp),
            )
            return True
