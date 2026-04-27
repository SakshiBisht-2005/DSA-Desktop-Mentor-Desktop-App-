from __future__ import annotations

import random

from app.services.course_service import CourseService


LANGUAGE_KEYWORDS = {
    "Python": {
        "keywords": {"def", "return", "for", "while", "if", "elif", "else", "in", "True", "False", "None", "class", "import", "from"},
        "builtins": {"len", "range", "enumerate", "max", "min", "sum", "set", "dict", "list"},
        "comments": "#",
    },
    "C++": {
        "keywords": {"auto", "bool", "class", "const", "else", "for", "if", "int", "return", "using", "vector", "while"},
        "builtins": {"push_back", "unordered_map", "priority_queue", "string", "max", "min"},
        "comments": "//",
    },
    "Java": {
        "keywords": {"class", "if", "else", "for", "while", "return", "int", "boolean", "public", "private", "new"},
        "builtins": {"ArrayList", "HashMap", "Math", "List", "Map", "Queue", "Deque"},
        "comments": "//",
    },
}


class QuestionEngineService:
    def __init__(self, course_service: CourseService) -> None:
        self.course_service = course_service

    def search(
        self,
        accessible_topics: list[str],
        *,
        query: str = "",
        difficulty: str = "All",
    ) -> list[dict]:
        return self.course_service.search_problems(
            query=query,
            difficulty=difficulty,
            topic_slugs=accessible_topics,
        )

    def random_problem(
        self,
        topic_slugs: list[str],
        *,
        difficulty: str = "All",
    ) -> dict | None:
        pool = self.course_service.search_problems(
            difficulty=difficulty,
            topic_slugs=topic_slugs,
        )
        return random.choice(pool) if pool else None

    def evaluate_code(self, problem: dict, language: str, code: str) -> dict:
        keywords = problem["solution_keywords"][language]
        cleaned = code.lower()
        hits = [keyword for keyword in keywords if keyword.lower() in cleaned]
        coverage = len(hits) / max(1, len(keywords))
        length_bonus = 0.15 if len(code.strip()) >= 80 else 0.0
        score = min(100.0, round((coverage + length_bonus) * 100, 1))
        missing = [keyword for keyword in keywords if keyword not in hits]
        if score >= 85:
            feedback = "Strong structural attempt. Your code reflects the intended invariant and data structure."
        elif score >= 65:
            feedback = "Promising direction. The main pattern is visible, but the mentor still expects tighter execution."
        else:
            feedback = "This attempt is still too vague. Revisit the optimized approach and tighten the core state transitions."
        if missing:
            feedback += "\nFocus on these missing ideas: " + ", ".join(missing[:4])
        console = self.run_preview(problem, language, code, score, hits)
        return {
            "score": score,
            "feedback": feedback,
            "console": console,
            "matched_keywords": hits,
        }

    def run_preview(
        self,
        problem: dict,
        language: str,
        code: str,
        score: float | None = None,
        hits: list[str] | None = None,
    ) -> str:
        lines = [
            f"Language: {language}",
            f"Pattern: {problem['pattern']}",
            "Sample cases:",
        ]
        for case in problem["test_cases"][:3]:
            lines.append(f"  input  -> {case['input']}")
            lines.append(f"  output -> {case['output']}")
        if score is not None:
            lines.append("")
            lines.append(f"Structural score: {score:.1f}")
        if hits:
            lines.append("Detected signals: " + ", ".join(hits[:6]))
        if len(code.strip()) < 20:
            lines.append("Warning: this draft is still very short for an interview-ready answer.")
        lines.append("Preview mode checks structure and expected outputs; it does not compile external languages.")
        return "\n".join(lines)

    def syntax_profile(self, language: str) -> dict[str, object]:
        return LANGUAGE_KEYWORDS[language]
