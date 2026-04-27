from __future__ import annotations

from copy import deepcopy

from app.core.config import TOPIC_ORDER
from app.data.course_data import TOPICS


class CourseService:
    def __init__(self) -> None:
        self.topics = deepcopy(TOPICS)
        self.topic_map = {topic["slug"]: topic for topic in self.topics}
        self.problem_map: dict[str, tuple[dict, dict]] = {}
        for topic in self.topics:
            for problem in topic["practice"]:
                self.problem_map[problem["id"]] = (topic, problem)

    def topic_order(self) -> list[str]:
        return list(TOPIC_ORDER)

    def list_topics(self) -> list[dict]:
        return self.topics

    def get_topic(self, topic_slug: str) -> dict:
        return self.topic_map[topic_slug]

    def get_topic_index(self, topic_slug: str) -> int:
        return self.topic_order().index(topic_slug)

    def get_problem(self, problem_id: str) -> tuple[dict, dict]:
        return self.problem_map[problem_id]

    def problems_for_topic(self, topic_slug: str) -> list[dict]:
        return list(self.topic_map[topic_slug]["practice"])

    def list_problem_cards(self) -> list[dict]:
        cards = []
        for topic in self.topics:
            for problem in topic["practice"]:
                cards.append(
                    {
                        "problem_id": problem["id"],
                        "topic_slug": topic["slug"],
                        "topic_title": topic["title"],
                        "group": topic["group"],
                        "subtopic": problem["subtopic"],
                        "title": problem["title"],
                        "difficulty": problem["difficulty"],
                        "pattern": problem["pattern"],
                    }
                )
        return cards

    def search_problems(
        self,
        *,
        query: str = "",
        difficulty: str = "All",
        topic_slugs: list[str] | None = None,
    ) -> list[dict]:
        query = query.strip().lower()
        allowed_topics = set(topic_slugs) if topic_slugs else None
        results = []
        for topic in self.topics:
            if allowed_topics is not None and topic["slug"] not in allowed_topics:
                continue
            for problem in topic["practice"]:
                if difficulty != "All" and problem["difficulty"] != difficulty:
                    continue
                haystack = " ".join(
                    [
                        topic["title"],
                        problem["title"],
                        problem["subtopic"],
                        problem["statement"],
                        problem["pattern"],
                    ]
                ).lower()
                if query and query not in haystack:
                    continue
                results.append(
                    {
                        "problem_id": problem["id"],
                        "topic_slug": topic["slug"],
                        "topic_title": topic["title"],
                        "title": problem["title"],
                        "difficulty": problem["difficulty"],
                        "subtopic": problem["subtopic"],
                        "pattern": problem["pattern"],
                    }
                )
        return results

    def topic_tree(self) -> list[dict]:
        return [
            {
                "slug": topic["slug"],
                "title": topic["title"],
                "group": topic["group"],
                "subtopics": topic["subtopics"],
                "problem_count": len(topic["practice"]),
            }
            for topic in self.topics
        ]

    def group_map(self) -> dict[str, list[dict]]:
        groups: dict[str, list[dict]] = {}
        for topic in self.topics:
            groups.setdefault(topic["group"], []).append(topic)
        return groups

    def recommended_path(self) -> list[dict]:
        path = []
        for index, slug in enumerate(self.topic_order(), start=1):
            topic = self.get_topic(slug)
            path.append(
                {
                    "step": index,
                    "slug": slug,
                    "title": topic["title"],
                    "focus": ", ".join(topic["subtopics"][:2]),
                    "problem_count": len(topic["practice"]),
                }
            )
        return path

    def breadcrumb(self, topic_slug: str, problem_id: str | None = None) -> str:
        topic = self.get_topic(topic_slug)
        if not problem_id:
            return f"{topic['title']}"
        _topic, problem = self.get_problem(problem_id)
        return f"{topic['title']} > {problem['subtopic']} > {problem['title']}"

    def build_test_questions(self, topic_slugs: list[str], selected_language: str) -> list[dict]:
        questions: list[dict] = []
        for topic_slug in topic_slugs:
            topic = self.get_topic(topic_slug)
            for mcq in topic["mcqs"][:2]:
                questions.append(
                    {
                        "id": mcq["id"],
                        "type": "mcq",
                        "topic_slug": topic_slug,
                        "title": topic["title"],
                        "prompt": mcq["prompt"],
                        "options": mcq["options"],
                        "answer_index": mcq["answer_index"],
                        "explanation": mcq["explanation"],
                    }
                )
        if topic_slugs:
            last_topic = self.get_topic(topic_slugs[-1])
            coding_problem = next(
                (problem for problem in last_topic["practice"] if problem["difficulty"] == "Medium"),
                last_topic["practice"][0],
            )
            questions.append(
                {
                    "id": f"test-{coding_problem['id']}",
                    "type": "coding",
                    "topic_slug": last_topic["slug"],
                    "title": coding_problem["title"],
                    "prompt": coding_problem["statement"],
                    "difficulty": coding_problem["difficulty"],
                    "examples": coding_problem["examples"],
                    "test_cases": coding_problem["test_cases"],
                    "solution_keywords": coding_problem["solution_keywords"][selected_language],
                    "reference_solution": coding_problem["solution"][selected_language],
                    "language": selected_language,
                }
            )
        return questions
