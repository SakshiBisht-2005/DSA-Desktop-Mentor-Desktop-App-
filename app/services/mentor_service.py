from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime

from app.core.config import PASSING_SCORE
from app.core.models import DashboardSnapshot, TestState, TopicState
from app.repositories.learning_repository import LearningRepository
from app.services.course_service import CourseService
from app.services.question_engine import QuestionEngineService


class MentorService:
    def __init__(
        self,
        learning_repository: LearningRepository,
        course_service: CourseService,
        question_engine: QuestionEngineService,
    ) -> None:
        self.learning_repository = learning_repository
        self.course_service = course_service
        self.question_engine = question_engine

    def get_topic_states(self, user_id: int) -> list[TopicState]:
        rows = self.learning_repository.get_progress_rows(user_id)
        states: list[TopicState] = []
        title_lookup = {topic["slug"]: topic["title"] for topic in self.course_service.list_topics()}
        for row in rows:
            states.append(
                TopicState(
                    slug=row["topic_slug"],
                    title=title_lookup[row["topic_slug"]],
                    index=row["topic_index"],
                    unlocked=bool(row["unlocked"]),
                    completed=bool(row["completed"]),
                    needs_revision=bool(row["needs_revision"]),
                    last_studied_on=row["last_studied_on"],
                    completed_on=row["completed_on"],
                )
            )
        return states

    def get_accessible_topics(self, user_id: int, selected_language: str) -> list[str]:
        states = self.get_topic_states(user_id)
        accessible: list[str] = []
        for state in states:
            allowed, _ = self.can_access_topic(user_id, state.slug, selected_language)
            if state.completed or allowed:
                accessible.append(state.slug)
        return accessible

    def get_completed_topics(self, user_id: int) -> list[str]:
        return [state.slug for state in self.get_topic_states(user_id) if state.completed]

    def get_active_test(self, user_id: int, selected_language: str) -> TestState | None:
        active_row = self.learning_repository.get_active_test(user_id)
        if active_row:
            return self._build_test_state(active_row)

        latest_passed = self.learning_repository.get_latest_passed_test(user_id)
        anchor_date = None
        if latest_passed:
            anchor_dates = json.loads(latest_passed["study_dates_json"])
            anchor_date = anchor_dates[-1] if anchor_dates else None

        pending_dates = self.learning_repository.get_distinct_study_dates_after(user_id, anchor_date)
        if len(pending_dates) < 2:
            return None

        study_window = pending_dates[:2]
        topics = self.learning_repository.get_topics_for_dates(user_id, study_window)
        if not topics:
            return None
        coverage_key = "|".join(study_window)
        questions = self.course_service.build_test_questions(topics, selected_language)
        test_id = self.learning_repository.create_test(
            user_id=user_id,
            coverage_key=coverage_key,
            status="due",
            topics=topics,
            study_dates=study_window,
            questions=questions,
            created_at=self._now(),
        )
        return self._build_test_state(self.learning_repository.get_test_by_id(user_id, test_id))

    def can_access_topic(self, user_id: int, topic_slug: str, selected_language: str) -> tuple[bool, str]:
        states = self.get_topic_states(user_id)
        active_test = self.get_active_test(user_id, selected_language)
        state_map = {state.slug: state for state in states}
        requested = state_map[topic_slug]

        if active_test:
            if requested.completed or topic_slug in active_test.topics:
                return True, ""
            return False, "Strict mentor lock: pass your pending test before starting a new incomplete topic."

        first_incomplete = next((state for state in states if not state.completed), None)
        if not first_incomplete:
            return True, ""
        if requested.index <= first_incomplete.index:
            return True, ""
        return False, "Complete the previous topic before moving ahead."

    def record_topic_study(self, user_id: int, topic_slug: str, selected_language: str) -> None:
        allowed, message = self.can_access_topic(user_id, topic_slug, selected_language)
        if not allowed:
            raise ValueError(message)
        timestamp = self._now()
        today = self._today()
        self.learning_repository.update_topic_flags(
            user_id,
            topic_slug,
            started_on=timestamp,
            last_studied_on=timestamp,
        )
        self.learning_repository.record_study_session(
            user_id,
            topic_slug,
            studied_on=timestamp,
            session_date=today,
            action="study",
        )
        self._clear_revision_if_needed(user_id, topic_slug, timestamp)

    def mark_topic_completed(self, user_id: int, topic_slug: str, selected_language: str) -> None:
        allowed, message = self.can_access_topic(user_id, topic_slug, selected_language)
        if not allowed:
            raise ValueError(message)
        timestamp = self._now()
        today = self._today()
        self.learning_repository.update_topic_flags(
            user_id,
            topic_slug,
            completed=True,
            unlocked=True,
            needs_revision=False,
            started_on=timestamp,
            completed_on=timestamp,
            last_studied_on=timestamp,
        )
        self.learning_repository.record_study_session(
            user_id,
            topic_slug,
            studied_on=timestamp,
            session_date=today,
            action="complete",
        )
        next_slug = self._next_topic_slug(topic_slug)
        if next_slug:
            self.learning_repository.update_topic_flags(user_id, next_slug, unlocked=True)
        self.get_active_test(user_id, selected_language)

    def get_topic_note(self, user_id: int, topic_slug: str) -> str:
        return self.learning_repository.get_note(user_id, topic_slug)

    def save_topic_note(self, user_id: int, topic_slug: str, content: str) -> None:
        self.learning_repository.save_note(user_id, topic_slug, content, self._now())

    def get_problem_workspace(
        self,
        user_id: int,
        topic_slug: str,
        problem_id: str,
        selected_language: str,
    ) -> dict:
        _topic, problem = self.course_service.get_problem(problem_id)
        saved = self.learning_repository.get_practice_attempt(user_id, problem_id)
        default_console = self.question_engine.run_preview(
            problem,
            selected_language,
            saved["code"] if saved and saved["code"] else problem["starter_code"][selected_language],
        )
        return {
            "problem": problem,
            "saved_code": saved["code"] if saved and saved["code"] else problem["starter_code"][selected_language],
            "saved_feedback": saved["feedback"] if saved else "",
            "score": saved["score"] if saved else 0,
            "bookmarked": self.learning_repository.is_bookmarked(user_id, problem_id),
            "viewed_solution": bool(saved["viewed_solution"]) if saved else False,
            "console": default_console,
        }

    def save_practice_draft(
        self,
        user_id: int,
        topic_slug: str,
        problem_id: str,
        code: str,
    ) -> None:
        self.learning_repository.save_practice_draft(
            user_id,
            topic_slug,
            problem_id,
            code,
            self._now(),
        )

    def preview_practice_attempt(
        self,
        user_id: int,
        topic_slug: str,
        problem_id: str,
        selected_language: str,
        code: str,
    ) -> dict:
        allowed, message = self.can_access_topic(user_id, topic_slug, selected_language)
        if not allowed:
            raise ValueError(message)
        _topic, problem = self.course_service.get_problem(problem_id)
        evaluation = self.question_engine.evaluate_code(problem, selected_language, code)
        self.save_practice_draft(user_id, topic_slug, problem_id, code)
        return evaluation

    def submit_practice_attempt(
        self,
        user_id: int,
        topic_slug: str,
        problem_id: str,
        selected_language: str,
        code: str,
    ) -> dict:
        allowed, message = self.can_access_topic(user_id, topic_slug, selected_language)
        if not allowed:
            raise ValueError(message)
        topic, problem = self.course_service.get_problem(problem_id)
        evaluation = self.question_engine.evaluate_code(problem, selected_language, code)
        timestamp = self._now()
        self.learning_repository.save_practice_attempt(
            user_id=user_id,
            topic_slug=topic["slug"],
            problem_id=problem_id,
            code=code,
            feedback=evaluation["feedback"],
            score=evaluation["score"],
            viewed_solution=False,
            last_submitted_at=timestamp,
        )
        self.learning_repository.record_study_session(
            user_id,
            topic["slug"],
            studied_on=timestamp,
            session_date=self._today(),
            action="practice",
        )
        self._clear_revision_if_needed(user_id, topic["slug"], timestamp)
        self.get_active_test(user_id, selected_language)
        return evaluation

    def mark_solution_viewed(self, user_id: int, topic_slug: str, problem_id: str) -> None:
        self.learning_repository.mark_solution_viewed(
            user_id,
            topic_slug,
            problem_id,
            self._now(),
        )

    def toggle_bookmark(self, user_id: int, topic_slug: str, problem_id: str) -> bool:
        return self.learning_repository.toggle_bookmark(
            user_id,
            topic_slug,
            problem_id,
            self._now(),
        )

    def get_bookmarks(self, user_id: int) -> list[dict]:
        results: list[dict] = []
        for row in self.learning_repository.get_bookmarks(user_id):
            topic, problem = self.course_service.get_problem(row["problem_id"])
            results.append(
                {
                    "problem_id": row["problem_id"],
                    "topic_slug": row["topic_slug"],
                    "topic_title": topic["title"],
                    "title": problem["title"],
                    "difficulty": problem["difficulty"],
                    "subtopic": problem["subtopic"],
                }
            )
        return results

    def get_test_history(self, user_id: int) -> list[TestState]:
        rows = self.learning_repository.get_test_history(user_id)
        return [self._build_test_state(row) for row in rows]

    def submit_test(
        self,
        user_id: int,
        test_id: int,
        selected_language: str,
        answers: list[dict],
    ) -> dict:
        row = self.learning_repository.get_test_by_id(user_id, test_id)
        if not row:
            raise ValueError("Test not found.")
        state = self._build_test_state(row)

        if state.status == "revision_required":
            unresolved = [
                topic.slug
                for topic in self.get_topic_states(user_id)
                if topic.needs_revision and topic.slug in state.topics
            ]
            if unresolved:
                topic_names = [self.course_service.get_topic(slug)["title"] for slug in unresolved]
                raise ValueError("Revise these topics before retaking the test: " + ", ".join(topic_names))

        total_weight = 0
        earned = 0.0
        feedback: list[dict] = []

        for question in state.questions:
            answer = next((item for item in answers if item["id"] == question["id"]), {"value": ""})
            if question["type"] == "mcq":
                weight = 15
                total_weight += weight
                correct = str(answer["value"]).strip() == str(question["answer_index"])
                if correct:
                    earned += weight
                feedback.append(
                    {
                        "id": question["id"],
                        "type": "mcq",
                        "correct": correct,
                        "message": question["explanation"],
                    }
                )
                continue

            weight = 40
            total_weight += weight
            proxy_problem = {
                "pattern": question["title"],
                "solution_keywords": {selected_language: question["solution_keywords"]},
                "test_cases": question["test_cases"],
            }
            evaluation = self.question_engine.evaluate_code(proxy_problem, selected_language, str(answer["value"]))
            earned += weight * (evaluation["score"] / 100)
            feedback.append(
                {
                    "id": question["id"],
                    "type": "coding",
                    "correct": evaluation["score"] >= 70,
                    "message": evaluation["feedback"],
                    "reference": question["reference_solution"],
                }
            )

        percentage = round((earned / total_weight) * 100, 1) if total_weight else 0.0
        passed = percentage >= PASSING_SCORE
        status = "passed" if passed else "revision_required"
        self.learning_repository.update_test(
            test_id=test_id,
            status=status,
            score=percentage,
            passed=passed,
            answers=answers,
            feedback=feedback,
            attempts=state.attempts + 1,
            updated_at=self._now(),
        )

        for topic_slug in state.topics:
            self.learning_repository.update_topic_flags(
                user_id,
                topic_slug,
                needs_revision=not passed,
            )

        return {
            "passed": passed,
            "score": percentage,
            "feedback": feedback,
            "topics": state.topics,
        }

    def get_dashboard_snapshot(self, user_id: int, selected_language: str) -> DashboardSnapshot:
        topic_states = self.get_topic_states(user_id)
        completed_topics = sum(1 for topic in topic_states if topic.completed)
        active_test = self.get_active_test(user_id, selected_language)
        test_history = [self._test_summary(test) for test in self.get_test_history(user_id)[:5]]
        current_topic = next((topic.title for topic in topic_states if not topic.completed), "Course finished")

        weakness_counts: Counter[str] = Counter()
        for topic in topic_states:
            if topic.needs_revision:
                weakness_counts[topic.title] += 2
        for row in self.learning_repository.get_practice_rows(user_id):
            if row["score"] < 70:
                weakness_counts[self.course_service.get_topic(row["topic_slug"])["title"]] += 1

        weak_areas = [title for title, _ in weakness_counts.most_common(4)] or ["No weak areas flagged yet. Keep the streak going."]

        if active_test:
            if active_test.status == "revision_required":
                study_message = "Revision required before the next unlock."
            else:
                study_message = "A mentor test is ready based on your last two study days."
        else:
            pending_dates = self.learning_repository.get_distinct_study_dates_after(
                user_id,
                self._last_passed_anchor(user_id),
            )
            remaining = max(0, 2 - len(pending_dates))
            study_message = "Study today to move toward your next mentor test." if remaining else "Keep practicing completed topics while your next test is prepared."

        return DashboardSnapshot(
            completed_topics=completed_topics,
            total_topics=len(topic_states),
            completion_percent=round((completed_topics / len(topic_states)) * 100, 1),
            current_topic=current_topic,
            weak_areas=weak_areas,
            test_history=test_history,
            active_test=active_test,
            study_message=study_message,
        )

    def profile_snapshot(self, user_id: int, selected_language: str) -> dict:
        topic_states = self.get_topic_states(user_id)
        completed = [topic.title for topic in topic_states if topic.completed]
        revisions = [topic.title for topic in topic_states if topic.needs_revision]
        attempts = self.learning_repository.get_practice_rows(user_id)
        score_rows = [row["score"] for row in attempts if row["score"] is not None]
        average_score = round(sum(score_rows) / len(score_rows), 1) if score_rows else 0.0
        return {
            "completed_topics": completed,
            "revision_topics": revisions,
            "average_practice_score": average_score,
            "practice_attempts": len(attempts),
            "recommended_path": self.course_service.recommended_path(),
            "bookmarks": self.get_bookmarks(user_id),
            "active_test": self.get_active_test(user_id, selected_language),
        }

    def should_show_daily_reminder(self, user_id: int) -> bool:
        today = self._today()
        dates = self.learning_repository.get_distinct_study_dates_after(user_id, None)
        return today not in dates

    def _test_summary(self, test: TestState) -> dict:
        topic_titles = [self.course_service.get_topic(slug)["title"] for slug in test.topics]
        return {
            "id": test.test_id,
            "status": test.status.replace("_", " ").title(),
            "score": "-" if test.score is None else f"{test.score:.1f}",
            "topics": ", ".join(topic_titles),
            "attempts": test.attempts,
        }

    def _build_test_state(self, row) -> TestState:
        return TestState(
            test_id=row["id"],
            status=row["status"],
            score=row["score"],
            passed=bool(row["passed"]),
            attempts=row["attempts"],
            topics=json.loads(row["topics_json"]),
            study_dates=json.loads(row["study_dates_json"]),
            questions=json.loads(row["questions_json"]),
            answers=json.loads(row["answers_json"]) if row["answers_json"] else [],
            feedback=json.loads(row["feedback_json"]) if row["feedback_json"] else [],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _clear_revision_if_needed(self, user_id: int, topic_slug: str, timestamp: str) -> None:
        active_test = self.learning_repository.get_active_test(user_id)
        if active_test and active_test["status"] == "revision_required":
            topics = json.loads(active_test["topics_json"])
            if topic_slug in topics:
                self.learning_repository.update_topic_flags(
                    user_id,
                    topic_slug,
                    needs_revision=False,
                    last_studied_on=timestamp,
                )

    def _last_passed_anchor(self, user_id: int) -> str | None:
        passed = self.learning_repository.get_latest_passed_test(user_id)
        if not passed:
            return None
        dates = json.loads(passed["study_dates_json"])
        return dates[-1] if dates else None

    def _next_topic_slug(self, topic_slug: str) -> str | None:
        order = self.course_service.topic_order()
        index = order.index(topic_slug)
        if index + 1 >= len(order):
            return None
        return order[index + 1]

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _today() -> str:
        return date.today().isoformat()
