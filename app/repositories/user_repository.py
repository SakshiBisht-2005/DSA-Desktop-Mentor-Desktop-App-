from __future__ import annotations

from app.core.config import DEFAULT_LANGUAGE, DEFAULT_THEME
from app.core.database import DatabaseManager


class UserRepository:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def create_user(
        self,
        username: str,
        password_hash: str,
        created_at: str,
        selected_language: str = DEFAULT_LANGUAGE,
        theme: str = DEFAULT_THEME,
        reminders_enabled: bool = True,
        onboarding_seen: bool = False,
    ) -> int:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username, password_hash, selected_language, theme,
                    reminders_enabled, onboarding_seen, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    selected_language,
                    theme,
                    int(reminders_enabled),
                    int(onboarding_seen),
                    created_at,
                ),
            )
            return int(cursor.lastrowid)

    def get_by_username(self, username: str):
        with self.database.connect() as connection:
            return connection.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,),
            ).fetchone()

    def get_by_id(self, user_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

    def update_last_login(self, user_id: int, last_login_at: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE users SET last_login_at = ? WHERE id = ?",
                (last_login_at, user_id),
            )

    def update_preferences(
        self,
        user_id: int,
        selected_language: str | None = None,
        theme: str | None = None,
        reminders_enabled: bool | None = None,
        onboarding_seen: bool | None = None,
    ) -> None:
        fields = []
        values = []
        if selected_language is not None:
            fields.append("selected_language = ?")
            values.append(selected_language)
        if theme is not None:
            fields.append("theme = ?")
            values.append(theme)
        if reminders_enabled is not None:
            fields.append("reminders_enabled = ?")
            values.append(int(reminders_enabled))
        if onboarding_seen is not None:
            fields.append("onboarding_seen = ?")
            values.append(int(onboarding_seen))
        if not fields:
            return
        values.append(user_id)
        with self.database.connect() as connection:
            connection.execute(
                f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
                tuple(values),
            )
