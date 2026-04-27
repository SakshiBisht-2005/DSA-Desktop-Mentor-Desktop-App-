from __future__ import annotations

from datetime import datetime

from app.core.models import UserSession
from app.core.security import hash_password, verify_password
from app.repositories.learning_repository import LearningRepository
from app.repositories.user_repository import UserRepository
from app.services.course_service import CourseService


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        learning_repository: LearningRepository,
        course_service: CourseService,
    ) -> None:
        self.user_repository = user_repository
        self.learning_repository = learning_repository
        self.course_service = course_service

    def signup(self, username: str, password: str) -> UserSession:
        username = username.strip()
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if self.user_repository.get_by_username(username):
            raise ValueError("That username is already taken.")

        created_at = datetime.now().isoformat(timespec="seconds")
        user_id = self.user_repository.create_user(
            username=username,
            password_hash=hash_password(password),
            created_at=created_at,
        )
        self.learning_repository.initialize_progress(user_id, self.course_service.topic_order())
        row = self.user_repository.get_by_id(user_id)
        return self._build_session(row)

    def login(self, username: str, password: str) -> UserSession:
        row = self.user_repository.get_by_username(username.strip())
        if not row or not verify_password(password, row["password_hash"]):
            raise ValueError("Invalid username or password.")
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.user_repository.update_last_login(row["id"], timestamp)
        refreshed = self.user_repository.get_by_id(row["id"])
        return self._build_session(refreshed)

    def refresh_session(self, user_id: int) -> UserSession:
        row = self.user_repository.get_by_id(user_id)
        return self._build_session(row)

    def update_preferences(
        self,
        user_id: int,
        *,
        selected_language: str | None = None,
        theme: str | None = None,
        reminders_enabled: bool | None = None,
        onboarding_seen: bool | None = None,
    ) -> UserSession:
        self.user_repository.update_preferences(
            user_id,
            selected_language=selected_language,
            theme=theme,
            reminders_enabled=reminders_enabled,
            onboarding_seen=onboarding_seen,
        )
        return self.refresh_session(user_id)

    def _build_session(self, row) -> UserSession:
        return UserSession(
            user_id=row["id"],
            username=row["username"],
            selected_language=row["selected_language"],
            theme=row["theme"],
            reminders_enabled=bool(row["reminders_enabled"]),
            onboarding_seen=bool(row["onboarding_seen"]),
        )
