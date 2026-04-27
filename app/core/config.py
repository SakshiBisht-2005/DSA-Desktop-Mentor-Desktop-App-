from pathlib import Path

APP_NAME = "DSA Mentor Studio"
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "dsa_mentor.db"

LANGUAGES = ("Python", "C++", "Java")
TOPIC_ORDER = (
    "arrays",
    "strings",
    "linked_list",
    "stack",
    "queue",
    "recursion_backtracking",
    "searching_sorting",
    "hashing",
    "two_pointers_sliding_window",
    "trees",
    "heap_priority_queue",
    "graphs",
    "dynamic_programming",
    "greedy_algorithms",
    "bit_manipulation",
)

PASSING_SCORE = 70
DEFAULT_THEME = "dark"
DEFAULT_LANGUAGE = "Python"
FONT_FAMILY = "Segoe UI"
CODE_FONT_FAMILY = "Consolas"
