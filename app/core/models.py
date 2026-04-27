from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class UserSession:
    user_id: int
    username: str
    selected_language: str
    theme: str
    reminders_enabled: bool
    onboarding_seen: bool


@dataclass(slots=True)
class TopicState:
    slug: str
    title: str
    index: int
    unlocked: bool
    completed: bool
    needs_revision: bool
    last_studied_on: str | None = None
    completed_on: str | None = None


@dataclass(slots=True)
class TestState:
    test_id: int
    status: str
    score: float | None
    passed: bool
    attempts: int
    topics: list[str] = field(default_factory=list)
    study_dates: list[str] = field(default_factory=list)
    questions: list[dict[str, Any]] = field(default_factory=list)
    answers: list[dict[str, Any]] = field(default_factory=list)
    feedback: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class DashboardSnapshot:
    completed_topics: int
    total_topics: int
    completion_percent: float
    current_topic: str
    weak_areas: list[str]
    test_history: list[dict[str, Any]]
    active_test: TestState | None
    study_message: str
