from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from app.core.config import APP_NAME, FONT_FAMILY, LANGUAGES
from app.core.database import DatabaseManager
from app.repositories.learning_repository import LearningRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.course_service import CourseService
from app.services.mentor_service import MentorService
from app.services.question_engine import QuestionEngineService
from app.ui.components.editor import CodeEditorPanel
from app.ui.components.tooltips import ToolTip
from app.ui.theme import ThemeController


def configure_tk_runtime() -> None:
    runtime_dir = Path(sys.executable).resolve().parent
    tcl_dir = runtime_dir / "tcl"
    dll_dir = runtime_dir / "DLLs"
    tcl_library = tcl_dir / "tcl8.6"
    tk_library = tcl_dir / "tk8.6"
    if dll_dir.exists():
        os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(dll_dir))
    if tcl_library.exists():
        os.environ.setdefault("TCL_LIBRARY", str(tcl_library))
    if tk_library.exists():
        os.environ.setdefault("TK_LIBRARY", str(tk_library))


def clear_children(widget: tk.Widget) -> None:
    for child in widget.winfo_children():
        child.destroy()


def set_text(widget: tk.Text, content: str, *, editable: bool = False) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", tk.END)
    widget.insert("1.0", content)
    widget.configure(state="normal" if editable else "disabled")


def make_button(
    parent: tk.Widget,
    text: str,
    command,
    palette: dict[str, str],
    *,
    kind: str = "secondary",
    width: int | None = None,
) -> tk.Button:
    bg = palette["card_alt"]
    fg = palette["text"]
    active_bg = palette["accent_soft"]
    if kind == "primary":
        bg = palette["accent"]
        fg = palette["panel"]
    elif kind == "danger":
        bg = palette["danger"]
        fg = "#ffffff"
        active_bg = palette["danger"]
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=fg,
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        width=width,
        padx=14,
        pady=9,
        font=(FONT_FAMILY, 10, "bold"),
    )


def make_entry(
    parent: tk.Widget,
    palette: dict[str, str],
    *,
    textvariable=None,
    show: str | None = None,
) -> tk.Entry:
    return tk.Entry(
        parent,
        textvariable=textvariable,
        bg=palette["editor"],
        fg=palette["text"],
        insertbackground=palette["text"],
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=palette["border"],
        highlightcolor=palette["accent"],
        font=(FONT_FAMILY, 10),
        show=show or "",
    )


def make_scrolled_text(theme: ThemeController, parent: tk.Widget, *, height: int, editable: bool) -> ScrolledText:
    widget = ScrolledText(parent, height=height, wrap="word")
    theme.style_text_widget(widget, editable=editable)
    return widget


def format_solution_content(problem: dict, language: str) -> str:
    sections = [
        "Why This Works",
        problem["solution_summary"],
        "",
        "Optimized Approach",
        problem["optimized_approach"],
        "",
        "Pseudo Code",
        problem["pseudo_code"],
        "",
        "Time Complexity",
        problem["optimized_time_complexity"],
        "",
        "Space Complexity",
        problem["optimized_space_complexity"],
        "",
        f"Optimized {language} Code",
        problem["solution"][language],
    ]
    return "\n".join(sections)


def difficulty_color(palette: dict[str, str], difficulty: str) -> str:
    return {
        "Easy": palette["success"],
        "Medium": palette["warning"],
        "Hard": palette["danger"],
    }.get(difficulty, palette["accent"])


class ScrollableFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, palette: dict[str, str]) -> None:
        super().__init__(parent, bg=palette["bg"])
        self.canvas = tk.Canvas(self, bg=palette["bg"], highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=palette["bg"])
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.window_id, width=event.width))


class OnboardingDialog(tk.Toplevel):
    def __init__(self, app: "DsaMentorApp", *, persistent: bool) -> None:
        super().__init__(app)
        self.app = app
        self.persistent = persistent
        self.palette = app.theme_controller.palette
        self.steps = [
            (
                "Welcome",
                "DSA Mentor Studio is structured like a guided training platform. The top navigation keeps you moving between dashboard, theory, practice, tests, and profile without losing context.",
            ),
            (
                "Roadmap",
                "Topics unlock in order. The roadmap tree shows groups, topics, and problem sets. You can revisit completed topics freely, but unfinished future topics stay locked until the mentor allows them.",
            ),
            (
                "Practice",
                "The practice screen is intentionally LeetCode-like: roadmap on the left, prompt in the center, and code editor plus output console on the right. Run previews inspect structure, while submit stores mentor feedback.",
            ),
            (
                "Mentor Mode",
                "Every two distinct study days trigger a test from the topics you touched. If you fail, those topics go into revision mode and must be revisited before the next unlock.",
            ),
        ]
        self.index = 0
        self.title("Quick Tour")
        self.transient(app)
        self.grab_set()
        self.configure(bg=self.palette["panel"])
        self.geometry("620x360")
        self.resizable(False, False)
        self._build()
        self._refresh()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        card = tk.Frame(self, bg=self.palette["panel"])
        card.pack(fill="both", expand=True, padx=24, pady=24)
        self.step_label = tk.Label(card, bg=self.palette["panel"], fg=self.palette["muted"], font=(FONT_FAMILY, 10, "bold"))
        self.step_label.pack(anchor="w")
        self.title_label = tk.Label(card, bg=self.palette["panel"], fg=self.palette["text"], font=(FONT_FAMILY, 22, "bold"))
        self.title_label.pack(anchor="w", pady=(12, 10))
        self.body_label = tk.Label(
            card,
            bg=self.palette["panel"],
            fg=self.palette["text"],
            justify="left",
            wraplength=540,
            font=(FONT_FAMILY, 11),
        )
        self.body_label.pack(anchor="w", fill="x")

        footer = tk.Frame(card, bg=self.palette["panel"])
        footer.pack(side="bottom", fill="x", pady=(28, 0))
        self.skip_button = make_button(footer, "Close", self._finish, self.palette)
        self.skip_button.pack(side="left")
        self.back_button = make_button(footer, "Back", self._back, self.palette)
        self.back_button.pack(side="right", padx=(8, 0))
        self.next_button = make_button(footer, "Next", self._next, self.palette, kind="primary")
        self.next_button.pack(side="right")

    def _refresh(self) -> None:
        title, body = self.steps[self.index]
        self.step_label.configure(text=f"Step {self.index + 1} of {len(self.steps)}")
        self.title_label.configure(text=title)
        self.body_label.configure(text=body)
        self.back_button.configure(state="normal" if self.index else "disabled")
        self.next_button.configure(text="Finish" if self.index == len(self.steps) - 1 else "Next")

    def _next(self) -> None:
        if self.index == len(self.steps) - 1:
            self._finish()
            return
        self.index += 1
        self._refresh()

    def _back(self) -> None:
        if self.index:
            self.index -= 1
            self._refresh()

    def _finish(self) -> None:
        if self.persistent:
            self.app.mark_onboarding_seen()
        self.destroy()


class TopicTreeFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, palette: dict[str, str], title: str) -> None:
        super().__init__(parent, bg=palette["card"], highlightthickness=1, highlightbackground=palette["border"])
        self.palette = palette
        self.title = title
        self._build()

    def _build(self) -> None:
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        tk.Label(self, text=self.title, bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 14, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        self.controls = tk.Frame(self, bg=self.palette["card"])
        self.controls.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        self.tree = ttk.Treeview(self, show="tree")
        self.tree.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))


class DsaMentorApp(tk.Tk):
    def __init__(
        self,
        auth_service: AuthService,
        mentor_service: MentorService,
        course_service: CourseService,
        question_engine: QuestionEngineService,
    ) -> None:
        configure_tk_runtime()
        super().__init__()
        self.auth_service = auth_service
        self.mentor_service = mentor_service
        self.course_service = course_service
        self.question_engine = question_engine
        self.session = None
        self.selected_topic_slug: str | None = None
        self.selected_problem_id: str | None = None
        self.current_page = "dashboard"
        self.practice_query = ""
        self.practice_difficulty = "All"
        self.title(APP_NAME)
        self.geometry("1540x940")
        self.minsize(1280, 780)
        self.theme_controller = ThemeController(self, "dark")
        self.content_frame: tk.Frame | None = None
        self.show_auth()

    def show_auth(self) -> None:
        self.session = None
        self.selected_topic_slug = None
        self.selected_problem_id = None
        self.practice_query = ""
        self.practice_difficulty = "All"
        self.current_page = "dashboard"
        self.theme_controller.set_mode("dark")
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = AuthScreen(self)
        self.content_frame.pack(fill="both", expand=True)

    def handle_session(self, session) -> None:
        self.session = session
        self.selected_topic_slug = self._first_incomplete_topic()
        self.selected_problem_id = self.course_service.problems_for_topic(self.selected_topic_slug)[0]["id"]
        self.current_page = "dashboard"
        self.rebuild_main_shell()
        if not self.session.onboarding_seen:
            self.after(120, lambda: OnboardingDialog(self, persistent=True))
        elif self.session.reminders_enabled and self.mentor_service.should_show_daily_reminder(self.session.user_id):
            self.after(
                120,
                lambda: messagebox.showinfo(
                    APP_NAME,
                    "Strict mentor reminder: log a real study session today so the mentor can keep your momentum alive.",
                    parent=self,
                ),
            )

    def rebuild_main_shell(self) -> None:
        if not self.session:
            return
        self.session = self.auth_service.refresh_session(self.session.user_id)
        self.theme_controller.set_mode(self.session.theme)
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = MainShell(self)
        self.content_frame.pack(fill="both", expand=True)

    def logout(self) -> None:
        self.show_auth()

    def change_language(self, selected_language: str) -> None:
        if not self.session or selected_language == self.session.selected_language:
            return
        self.session = self.auth_service.update_preferences(
            self.session.user_id,
            selected_language=selected_language,
        )
        self.rebuild_main_shell()

    def toggle_theme(self) -> None:
        if not self.session:
            return
        next_theme = "light" if self.session.theme == "dark" else "dark"
        self.session = self.auth_service.update_preferences(self.session.user_id, theme=next_theme)
        self.rebuild_main_shell()

    def toggle_reminders(self, enabled: bool) -> None:
        if not self.session:
            return
        self.session = self.auth_service.update_preferences(self.session.user_id, reminders_enabled=enabled)
        self.rebuild_main_shell()

    def mark_onboarding_seen(self) -> None:
        if not self.session:
            return
        self.session = self.auth_service.update_preferences(self.session.user_id, onboarding_seen=True)
        if isinstance(self.content_frame, MainShell):
            self.content_frame.refresh_all()

    def select_topic(self, topic_slug: str) -> None:
        self.selected_topic_slug = topic_slug
        if self.selected_problem_id:
            current_topic, _problem = self.course_service.get_problem(self.selected_problem_id)
            if current_topic["slug"] == topic_slug:
                return
        problems = self.course_service.problems_for_topic(topic_slug)
        if problems:
            self.selected_problem_id = problems[0]["id"]

    def select_problem(self, problem_id: str) -> None:
        topic, _problem = self.course_service.get_problem(problem_id)
        self.selected_problem_id = problem_id
        self.selected_topic_slug = topic["slug"]

    def set_practice_filters(self, *, query: str | None = None, difficulty: str | None = None) -> None:
        if query is not None:
            self.practice_query = query
        if difficulty is not None:
            self.practice_difficulty = difficulty

    def open_practice_search(self, query: str) -> None:
        self.practice_query = query
        if isinstance(self.content_frame, MainShell):
            self.content_frame.show_page("practice")
            practice_page = self.content_frame.pages["practice"]
            practice_page.refresh()

    def open_tutorial(self) -> None:
        if self.session and not self.session.onboarding_seen:
            self.mark_onboarding_seen()
        OnboardingDialog(self, persistent=False)

    def _first_incomplete_topic(self) -> str:
        states = self.mentor_service.get_topic_states(self.session.user_id)
        for state in states:
            if not state.completed:
                return state.slug
        return states[-1].slug


class AuthScreen(tk.Frame):
    def __init__(self, app: DsaMentorApp) -> None:
        super().__init__(app, bg=app.theme_controller.palette["bg"])
        self.app = app
        self.palette = app.theme_controller.palette
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        hero = tk.Frame(self, bg=self.palette["bg"])
        hero.grid(row=0, column=0, sticky="nsew", padx=(56, 24), pady=56)
        auth_card = tk.Frame(self, bg=self.palette["panel"], highlightthickness=1, highlightbackground=self.palette["border"])
        auth_card.grid(row=0, column=1, sticky="nsew", padx=(24, 56), pady=56)

        tk.Label(hero, text=APP_NAME, bg=self.palette["bg"], fg=self.palette["text"], font=(FONT_FAMILY, 30, "bold"), anchor="w").pack(fill="x", pady=(20, 14))
        tk.Label(
            hero,
            text="A disciplined DSA desktop coach with a guided roadmap, LeetCode-style practice, auto-triggered tests, and per-user progress tracking.",
            bg=self.palette["bg"],
            fg=self.palette["muted"],
            justify="left",
            wraplength=620,
            font=(FONT_FAMILY, 13),
        ).pack(fill="x", pady=(0, 20))
        for line in [
            "15 major DSA tracks with structured theory and curated interview problems",
            "Three-panel practice workspace with syntax highlighting and run preview",
            "Strict mentor gating: two study days trigger mandatory assessment",
            "Profile, bookmarks, notes, search, filters, and beginner onboarding",
        ]:
            tk.Label(hero, text=line, bg=self.palette["bg"], fg=self.palette["text"], anchor="w", font=(FONT_FAMILY, 11), pady=8).pack(fill="x")

        tk.Label(auth_card, text="Enter The Training Room", bg=self.palette["panel"], fg=self.palette["text"], font=(FONT_FAMILY, 22, "bold")).pack(pady=(30, 12))
        notebook = ttk.Notebook(auth_card)
        notebook.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        login_tab = tk.Frame(notebook, bg=self.palette["panel"])
        signup_tab = tk.Frame(notebook, bg=self.palette["panel"])
        notebook.add(login_tab, text="Login")
        notebook.add(signup_tab, text="Signup")
        self.login_status = tk.StringVar(value="")
        self.signup_status = tk.StringVar(value="")
        self._build_login_tab(login_tab)
        self._build_signup_tab(signup_tab)

    def _build_login_tab(self, parent: tk.Frame) -> None:
        tk.Label(parent, text="Username", bg=self.palette["panel"], fg=self.palette["muted"]).pack(anchor="w", pady=(18, 6))
        self.login_username = make_entry(parent, self.palette)
        self.login_username.pack(fill="x")
        tk.Label(parent, text="Password", bg=self.palette["panel"], fg=self.palette["muted"]).pack(anchor="w", pady=(18, 6))
        self.login_password = make_entry(parent, self.palette, show="*")
        self.login_password.pack(fill="x")
        make_button(parent, "Login", self._login, self.palette, kind="primary").pack(fill="x", pady=(22, 12))
        tk.Label(parent, textvariable=self.login_status, bg=self.palette["panel"], fg=self.palette["danger"], wraplength=340).pack(anchor="w")

    def _build_signup_tab(self, parent: tk.Frame) -> None:
        tk.Label(parent, text="Username", bg=self.palette["panel"], fg=self.palette["muted"]).pack(anchor="w", pady=(18, 6))
        self.signup_username = make_entry(parent, self.palette)
        self.signup_username.pack(fill="x")
        tk.Label(parent, text="Password", bg=self.palette["panel"], fg=self.palette["muted"]).pack(anchor="w", pady=(18, 6))
        self.signup_password = make_entry(parent, self.palette, show="*")
        self.signup_password.pack(fill="x")
        tk.Label(parent, text="Confirm Password", bg=self.palette["panel"], fg=self.palette["muted"]).pack(anchor="w", pady=(18, 6))
        self.signup_confirm = make_entry(parent, self.palette, show="*")
        self.signup_confirm.pack(fill="x")
        make_button(parent, "Create Account", self._signup, self.palette, kind="primary").pack(fill="x", pady=(22, 12))
        tk.Label(parent, textvariable=self.signup_status, bg=self.palette["panel"], fg=self.palette["danger"], wraplength=340).pack(anchor="w")

    def _login(self) -> None:
        self.login_status.set("")
        try:
            session = self.app.auth_service.login(self.login_username.get(), self.login_password.get())
        except ValueError as exc:
            self.login_status.set(str(exc))
            return
        self.app.handle_session(session)

    def _signup(self) -> None:
        self.signup_status.set("")
        if self.signup_password.get() != self.signup_confirm.get():
            self.signup_status.set("Passwords do not match.")
            return
        try:
            session = self.app.auth_service.signup(self.signup_username.get(), self.signup_password.get())
        except ValueError as exc:
            self.signup_status.set(str(exc))
            return
        self.app.handle_session(session)


class MainShell(tk.Frame):
    def __init__(self, app: DsaMentorApp) -> None:
        super().__init__(app, bg=app.theme_controller.palette["bg"])
        self.app = app
        self.palette = app.theme_controller.palette
        self.nav_buttons: dict[str, tk.Button] = {}
        self.pages: dict[str, object] = {}
        self.current_banner = tk.StringVar(value="")
        self.global_search_var = tk.StringVar(value=self.app.practice_query)
        self.language_var = tk.StringVar(value=self.app.session.selected_language)
        self.reminder_var = tk.BooleanVar(value=self.app.session.reminders_enabled)
        self._build()
        self.refresh_all()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._build_topbar()

        banner = tk.Label(
            self,
            textvariable=self.current_banner,
            bg=self.palette["bg"],
            fg=self.palette["warning"],
            font=(FONT_FAMILY, 10, "bold"),
            anchor="w",
        )
        banner.grid(row=1, column=0, sticky="ew", padx=22, pady=(8, 0))

        container = tk.Frame(self, bg=self.palette["bg"])
        container.grid(row=2, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.pages = {
            "dashboard": DashboardPage(container, self),
            "topics": TopicsPage(container, self),
            "practice": PracticePage(container, self),
            "tests": TestsPage(container, self),
            "profile": ProfilePage(container, self),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def _build_topbar(self) -> None:
        topbar = tk.Frame(self, bg=self.palette["panel"], height=76)
        topbar.grid(row=0, column=0, sticky="nsew")
        topbar.grid_propagate(False)
        topbar.columnconfigure(2, weight=1)
        tk.Label(topbar, text=APP_NAME, bg=self.palette["panel"], fg=self.palette["text"], font=(FONT_FAMILY, 18, "bold")).grid(row=0, column=0, sticky="w", padx=(24, 18))

        nav = tk.Frame(topbar, bg=self.palette["panel"])
        nav.grid(row=0, column=1, sticky="w")
        for key, label in [("dashboard", "Dashboard"), ("topics", "Topics"), ("practice", "Practice"), ("tests", "Tests"), ("profile", "Profile")]:
            button = make_button(nav, label, lambda name=key: self.show_page(name), self.palette)
            button.pack(side="left", padx=(0, 8))
            self.nav_buttons[key] = button
            ToolTip(button, f"Open the {label.lower()} workspace.")

        search_frame = tk.Frame(topbar, bg=self.palette["panel"])
        search_frame.grid(row=0, column=2, sticky="ew", padx=18)
        search_frame.columnconfigure(0, weight=1)
        search_entry = make_entry(search_frame, self.palette, textvariable=self.global_search_var)
        search_entry.grid(row=0, column=0, sticky="ew")
        search_entry.bind("<Return>", lambda _event: self._launch_search())
        search_button = make_button(search_frame, "Search", self._launch_search, self.palette)
        search_button.grid(row=0, column=1, padx=(8, 0))
        ToolTip(search_entry, "Search topics or problems and jump straight into the practice workspace.")

        controls = tk.Frame(topbar, bg=self.palette["panel"])
        controls.grid(row=0, column=3, sticky="e", padx=(0, 24))
        tk.Label(controls, text="Language", bg=self.palette["panel"], fg=self.palette["muted"]).pack(side="left", padx=(0, 6))
        language_combo = ttk.Combobox(controls, values=LANGUAGES, state="readonly", width=10, textvariable=self.language_var)
        language_combo.pack(side="left", padx=(0, 12))
        language_combo.bind("<<ComboboxSelected>>", lambda _event: self.app.change_language(self.language_var.get()))
        reminder_toggle = tk.Checkbutton(
            controls,
            text="Reminders",
            variable=self.reminder_var,
            command=lambda: self.app.toggle_reminders(self.reminder_var.get()),
            bg=self.palette["panel"],
            fg=self.palette["text"],
            activebackground=self.palette["panel"],
            activeforeground=self.palette["text"],
            selectcolor=self.palette["card"],
            font=(FONT_FAMILY, 10),
        )
        reminder_toggle.pack(side="left", padx=(0, 12))
        theme_button = make_button(controls, "Theme", self.app.toggle_theme, self.palette)
        theme_button.pack(side="left", padx=(0, 8))
        tutorial_button = make_button(controls, "Tutorial", self.app.open_tutorial, self.palette)
        tutorial_button.pack(side="left", padx=(0, 8))
        logout_button = make_button(controls, "Logout", self.app.logout, self.palette, kind="danger")
        logout_button.pack(side="left")
        ToolTip(theme_button, "Toggle between light and dark mode.")
        ToolTip(tutorial_button, "Reopen the first-time walkthrough.")

    def _launch_search(self) -> None:
        query = self.global_search_var.get().strip()
        self.app.open_practice_search(query)

    def refresh_all(self) -> None:
        snapshot = self.app.mentor_service.get_dashboard_snapshot(self.app.session.user_id, self.app.session.selected_language)
        self.current_banner.set(snapshot.study_message)
        if self.app.current_page in self.pages:
            self.show_page(self.app.current_page)

    def show_page(self, page_name: str) -> None:
        self.app.current_page = page_name
        self.pages[page_name].tkraise()
        self.pages[page_name].refresh()
        for key, button in self.nav_buttons.items():
            active = key == page_name
            button.configure(
                bg=self.palette["accent"] if active else self.palette["card_alt"],
                fg=self.palette["panel"] if active else self.palette["text"],
            )


class DashboardPage(tk.Frame):
    def __init__(self, parent: tk.Widget, shell: MainShell) -> None:
        super().__init__(parent, bg=shell.palette["bg"])
        self.shell = shell
        self.app = shell.app
        self.palette = shell.palette
        self._build()

    def _card(self, parent: tk.Widget, title: str) -> tuple[tk.Frame, tk.Label]:
        card = tk.Frame(parent, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        tk.Label(card, text=title, bg=self.palette["card"], fg=self.palette["muted"], font=(FONT_FAMILY, 10, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        value = tk.Label(card, text="-", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 19, "bold"), wraplength=280, justify="left")
        value.pack(anchor="w", padx=16, pady=(0, 14))
        return card, value

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        header = tk.Frame(self, bg=self.palette["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        tk.Label(header, text="Mentor Dashboard", bg=self.palette["bg"], fg=self.palette["text"], font=(FONT_FAMILY, 26, "bold")).pack(anchor="w")
        tk.Label(header, text="Recommended path first, disciplined practice second, and no random skipping.", bg=self.palette["bg"], fg=self.palette["muted"], font=(FONT_FAMILY, 11)).pack(anchor="w", pady=(6, 0))

        actions = tk.Frame(self, bg=self.palette["bg"])
        actions.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        make_button(actions, "Resume Topic", lambda: self.shell.show_page("topics"), self.palette, kind="primary").pack(side="left", padx=(0, 10))
        make_button(actions, "Open Practice", lambda: self.shell.show_page("practice"), self.palette).pack(side="left", padx=(0, 10))
        make_button(actions, "Mentor Test", lambda: self.shell.show_page("tests"), self.palette).pack(side="left")

        cards = tk.Frame(self, bg=self.palette["bg"])
        cards.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        cards.columnconfigure((0, 1, 2, 3), weight=1)
        card1, self.current_topic_value = self._card(cards, "Current Topic")
        card2, self.completion_value = self._card(cards, "Course Completion")
        card3, self.practice_value = self._card(cards, "Practice Average")
        card4, self.mode_value = self._card(cards, "Mentor Status")
        card1.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        card2.grid(row=0, column=1, sticky="ew", padx=8)
        card3.grid(row=0, column=2, sticky="ew", padx=8)
        card4.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        lower = tk.Frame(self, bg=self.palette["bg"])
        lower.grid(row=3, column=0, sticky="nsew")
        lower.columnconfigure(0, weight=3)
        lower.columnconfigure(1, weight=2)
        lower.rowconfigure(1, weight=1)

        roadmap = tk.Frame(lower, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        roadmap.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        roadmap.columnconfigure(0, weight=1)
        tk.Label(roadmap, text="Recommended Path", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 14, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        self.path_tree = ttk.Treeview(roadmap, columns=("focus", "count"), show="headings", height=8)
        self.path_tree.heading("focus", text="Primary Focus")
        self.path_tree.heading("count", text="Problems")
        self.path_tree.column("focus", width=460, anchor="w")
        self.path_tree.column("count", width=120, anchor="center")
        self.path_tree.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        progress_panel = tk.Frame(lower, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        progress_panel.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        tk.Label(progress_panel, text="Progress", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 14, "bold")).pack(anchor="w", padx=16, pady=(14, 10))
        self.progress_bar = ttk.Progressbar(progress_panel, maximum=100)
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 8))
        self.progress_label = tk.Label(progress_panel, text="", bg=self.palette["card"], fg=self.palette["muted"], font=(FONT_FAMILY, 10))
        self.progress_label.pack(anchor="w", padx=16, pady=(0, 10))
        tk.Label(progress_panel, text="Weak Areas", bg=self.palette["card"], fg=self.palette["muted"], font=(FONT_FAMILY, 10, "bold")).pack(anchor="w", padx=16, pady=(6, 6))
        self.weak_list = tk.Listbox(progress_panel, height=6, exportselection=False)
        self.app.theme_controller.style_listbox(self.weak_list)
        self.weak_list.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        history_panel = tk.Frame(lower, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        history_panel.grid(row=1, column=0, columnspan=2, sticky="nsew")
        history_panel.columnconfigure(0, weight=1)
        history_panel.rowconfigure(1, weight=1)
        tk.Label(history_panel, text="Recent Tests", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 14, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        self.history_tree = ttk.Treeview(history_panel, columns=("status", "score", "topics", "attempts"), show="headings", height=8)
        for column, label, width in [
            ("status", "Status", 180),
            ("score", "Score", 100),
            ("topics", "Topics", 560),
            ("attempts", "Attempts", 100),
        ]:
            self.history_tree.heading(column, text=label)
            self.history_tree.column(column, width=width, anchor="w")
        self.history_tree.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def refresh(self) -> None:
        dashboard = self.app.mentor_service.get_dashboard_snapshot(self.app.session.user_id, self.app.session.selected_language)
        profile = self.app.mentor_service.profile_snapshot(self.app.session.user_id, self.app.session.selected_language)
        self.current_topic_value.configure(text=dashboard.current_topic)
        self.completion_value.configure(text=f"{dashboard.completed_topics} / {dashboard.total_topics}")
        self.practice_value.configure(text=f"{profile['average_practice_score']:.1f}")
        self.mode_value.configure(
            text="Revision gate active" if dashboard.active_test and dashboard.active_test.status == "revision_required" else ("Test waiting" if dashboard.active_test else "Path open"),
            fg=self.palette["warning"] if dashboard.active_test else self.palette["success"],
        )
        self.progress_bar["value"] = dashboard.completion_percent
        self.progress_label.configure(text=f"{dashboard.completion_percent:.1f}% complete")

        self.weak_list.delete(0, tk.END)
        for item in dashboard.weak_areas:
            self.weak_list.insert(tk.END, item)

        for item in self.path_tree.get_children():
            self.path_tree.delete(item)
        for row in self.app.course_service.recommended_path():
            self.path_tree.insert("", tk.END, values=(f"{row['step']}. {row['title']} - {row['focus']}", row["problem_count"]))

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        history = dashboard.test_history or [{"status": "No tests yet", "score": "-", "topics": "Study on two distinct days to trigger the first mentor assessment.", "attempts": "-"}]
        for row in history:
            self.history_tree.insert("", tk.END, values=(row["status"], row["score"], row["topics"], row["attempts"]))


class TopicsPage(tk.Frame):
    def __init__(self, parent: tk.Widget, shell: MainShell) -> None:
        super().__init__(parent, bg=shell.palette["bg"])
        self.shell = shell
        self.app = shell.app
        self.palette = shell.palette
        self.topic_search_var = tk.StringVar()
        self._tree_syncing = False
        self._build()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.browser = TopicTreeFrame(self, self.palette, "Guided Roadmap")
        self.browser.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.topic_search = make_entry(self.browser.controls, self.palette, textvariable=self.topic_search_var)
        self.topic_search.pack(fill="x")
        self.topic_search.bind("<KeyRelease>", lambda _event: self.refresh())
        self.browser.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        ToolTip(self.topic_search, "Search the roadmap by topic name or subtopic.")

        right = tk.Frame(self, bg=self.palette["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        header = tk.Frame(right, bg=self.palette["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.topic_title = tk.Label(header, text="", bg=self.palette["bg"], fg=self.palette["text"], font=(FONT_FAMILY, 24, "bold"))
        self.topic_title.pack(anchor="w")
        self.topic_status = tk.Label(header, text="", bg=self.palette["bg"], fg=self.palette["muted"], font=(FONT_FAMILY, 10, "bold"))
        self.topic_status.pack(anchor="w", pady=(6, 10))
        actions = tk.Frame(header, bg=self.palette["bg"])
        actions.pack(anchor="w")
        self.study_button = make_button(actions, "Record Study Session", self._record_study, self.palette, kind="primary")
        self.study_button.pack(side="left", padx=(0, 8))
        self.complete_button = make_button(actions, "Mark Topic Complete", self._mark_complete, self.palette)
        self.complete_button.pack(side="left", padx=(0, 8))
        open_practice = make_button(actions, "Open In Practice", lambda: self.shell.show_page("practice"), self.palette)
        open_practice.pack(side="left")
        ToolTip(self.study_button, "Log a study session for today. Two study days trigger the next mentor test.")
        ToolTip(self.complete_button, "Mark the current topic complete once you are ready for the next unlock gate.")

        self.notebook = ttk.Notebook(right)
        self.notebook.grid(row=2, column=0, sticky="nsew")
        self.overview_tab = tk.Frame(self.notebook, bg=self.palette["card"])
        self.interview_tab = tk.Frame(self.notebook, bg=self.palette["card"])
        self.code_tab = tk.Frame(self.notebook, bg=self.palette["card"])
        self.notes_tab = tk.Frame(self.notebook, bg=self.palette["card"])
        self.ladder_tab = tk.Frame(self.notebook, bg=self.palette["card"])

        self.overview_text = make_scrolled_text(self.app.theme_controller, self.overview_tab, height=22, editable=False)
        self.interview_text = make_scrolled_text(self.app.theme_controller, self.interview_tab, height=22, editable=False)
        self.code_text = make_scrolled_text(self.app.theme_controller, self.code_tab, height=22, editable=False)
        self.notes_text = make_scrolled_text(self.app.theme_controller, self.notes_tab, height=22, editable=True)
        self.ladder_text = make_scrolled_text(self.app.theme_controller, self.ladder_tab, height=22, editable=False)

        for frame, text_widget, label in [
            (self.overview_tab, self.overview_text, "Overview"),
            (self.interview_tab, self.interview_text, "Interview"),
            (self.code_tab, self.code_text, "Code"),
            (self.notes_tab, self.notes_text, "Notes"),
            (self.ladder_tab, self.ladder_text, "Problem Ladder"),
        ]:
            frame.configure(bg=self.palette["card"])
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            self.notebook.add(frame, text=label)

        save_notes = make_button(right, "Save Notes", self._save_notes, self.palette)
        save_notes.grid(row=3, column=0, sticky="e", pady=(10, 0))

    def refresh(self) -> None:
        current_slug = self.app.selected_topic_slug or self.app.course_service.topic_order()[0]
        self._populate_tree(current_slug)
        topic = self.app.course_service.get_topic(current_slug)
        topic_state = next(state for state in self.app.mentor_service.get_topic_states(self.app.session.user_id) if state.slug == current_slug)
        allowed, lock_message = self.app.mentor_service.can_access_topic(self.app.session.user_id, current_slug, self.app.session.selected_language)
        status_parts = []
        if topic_state.completed:
            status_parts.append("Completed")
        elif topic_state.needs_revision:
            status_parts.append("Revision required")
        elif allowed:
            status_parts.append("Current guided topic")
        if not allowed:
            status_parts.append(lock_message)
        self.topic_title.configure(text=topic["title"])
        self.topic_status.configure(text=" | ".join(status_parts))
        self.study_button.configure(state="normal" if allowed else "disabled")
        self.complete_button.configure(state="normal" if allowed else "disabled")

        overview = [
            "Concept",
            topic["concept"],
            "",
            "Real-World Intuition",
            topic["real_world_intuition"],
            "",
            "Time Complexity",
            "\n".join(f"- {item}" for item in topic["time_complexity"]),
            "",
            "Space Complexity",
            topic["space_complexity"],
            "",
            "Alternative Approaches",
            "\n".join(f"- {item}" for item in topic["alternative_approaches"]),
            "",
            "Subtopics",
            "\n".join(f"- {item}" for item in topic["subtopics"]),
        ]
        interview = [
            "Interview Explanation",
            topic["interview_pitch"],
            "",
            "Visual Intuition",
            topic["visual_intuition"],
        ]
        ladder = []
        for index, problem in enumerate(topic["practice"], start=1):
            ladder.extend(
                [
                    f"{index}. {problem['title']} ({problem['difficulty']})",
                    f"Subtopic: {problem['subtopic']}",
                    problem["statement"],
                    "",
                ]
            )
        set_text(self.overview_text, "\n".join(overview))
        set_text(self.interview_text, "\n".join(interview))
        set_text(self.code_text, topic["implementations"][self.app.session.selected_language])
        set_text(self.notes_text, self.app.mentor_service.get_topic_note(self.app.session.user_id, current_slug), editable=True)
        set_text(self.ladder_text, "\n".join(ladder))

    def _populate_tree(self, current_slug: str) -> None:
        tree = self.browser.tree
        self._tree_syncing = True
        try:
            for item in tree.get_children():
                tree.delete(item)
            query = self.topic_search_var.get().strip().lower()
            topic_states = {state.slug: state for state in self.app.mentor_service.get_topic_states(self.app.session.user_id)}
            for group, topics in self.app.course_service.group_map().items():
                group_id = f"group:{group}"
                tree.insert("", tk.END, iid=group_id, text=group, open=True)
                for topic in topics:
                    haystack = " ".join([topic["title"], *topic["subtopics"]]).lower()
                    if query and query not in haystack:
                        continue
                    state = topic_states[topic["slug"]]
                    badge = "Done" if state.completed else ("Revise" if state.needs_revision else "Now")
                    label = f"{topic['title']}  [{badge}]  {len(topic['practice'])} problems"
                    tree.insert(group_id, tk.END, iid=f"topic:{topic['slug']}", text=label, open=topic["slug"] == current_slug)
            target = f"topic:{current_slug}"
            if tree.exists(target):
                tree.selection_set(target)
                tree.focus(target)
        finally:
            self._tree_syncing = False

    def _on_tree_select(self, _event=None) -> None:
        if self._tree_syncing:
            return
        selection = self.browser.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        if item_id.startswith("topic:"):
            slug = item_id.split(":", 1)[1]
            self.app.select_topic(slug)
            self.refresh()

    def _record_study(self) -> None:
        try:
            self.app.mentor_service.record_topic_study(self.app.session.user_id, self.app.selected_topic_slug, self.app.session.selected_language)
        except ValueError as exc:
            messagebox.showwarning(APP_NAME, str(exc))
            return
        self.shell.refresh_all()

    def _mark_complete(self) -> None:
        try:
            self.app.mentor_service.mark_topic_completed(self.app.session.user_id, self.app.selected_topic_slug, self.app.session.selected_language)
        except ValueError as exc:
            messagebox.showwarning(APP_NAME, str(exc))
            return
        self.shell.refresh_all()
        active_test = self.app.mentor_service.get_active_test(self.app.session.user_id, self.app.session.selected_language)
        if active_test:
            messagebox.showinfo(APP_NAME, "A mentor test has been triggered. Pass it before unlocking the next unfinished topic.")

    def _save_notes(self) -> None:
        self.app.mentor_service.save_topic_note(self.app.session.user_id, self.app.selected_topic_slug, self.notes_text.get("1.0", tk.END).strip())
        messagebox.showinfo(APP_NAME, "Notes saved for this topic.")


class PracticePage(tk.Frame):
    def __init__(self, parent: tk.Widget, shell: MainShell) -> None:
        super().__init__(parent, bg=shell.palette["bg"])
        self.shell = shell
        self.app = shell.app
        self.palette = shell.palette
        self.difficulty_var = tk.StringVar(value=self.app.practice_difficulty)
        self.search_var = tk.StringVar(value=self.app.practice_query)
        self._browser_syncing = False
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        header = tk.Frame(self, bg=self.palette["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.breadcrumb_label = tk.Label(header, text="", bg=self.palette["bg"], fg=self.palette["muted"], font=(FONT_FAMILY, 10, "bold"))
        self.breadcrumb_label.pack(anchor="w")
        tk.Label(header, text="Practice Workspace", bg=self.palette["bg"], fg=self.palette["text"], font=(FONT_FAMILY, 26, "bold")).pack(anchor="w", pady=(6, 0))

        layout = ttk.Panedwindow(self, orient="horizontal")
        layout.grid(row=1, column=0, sticky="nsew")

        left = TopicTreeFrame(layout, self.palette, "Problem Browser")
        center = tk.Frame(layout, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        right = tk.Frame(layout, bg=self.palette["bg"])
        layout.add(left, weight=2)
        layout.add(center, weight=3)
        layout.add(right, weight=4)
        self.browser = left

        self.search_entry = make_entry(left.controls, self.palette, textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=(0, 8))
        filter_row = tk.Frame(left.controls, bg=self.palette["card"])
        filter_row.pack(fill="x")
        self.difficulty_combo = ttk.Combobox(filter_row, values=("All", "Easy", "Medium", "Hard"), state="readonly", width=10, textvariable=self.difficulty_var)
        self.difficulty_combo.pack(side="left")
        self.difficulty_combo.bind("<<ComboboxSelected>>", lambda _event: self._refresh_browser())
        self.random_button = make_button(filter_row, "Practice Mode", self._open_random_problem, self.palette, kind="primary")
        self.random_button.pack(side="right")
        ToolTip(self.random_button, "Jump to a random problem from completed topics.")
        self.search_entry.bind("<KeyRelease>", lambda _event: self._refresh_browser())
        self.browser.tree.bind("<<TreeviewSelect>>", self._on_browser_select)

        center.columnconfigure(0, weight=1)
        center.rowconfigure(2, weight=1)
        self.problem_title = tk.Label(center, text="", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 20, "bold"))
        self.problem_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        self.difficulty_chip = tk.Label(center, text="", bg=self.palette["accent"], fg=self.palette["panel"], font=(FONT_FAMILY, 9, "bold"), padx=10, pady=4)
        self.difficulty_chip.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        self.center_notebook = ttk.Notebook(center)
        self.center_notebook.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.description_tab = tk.Frame(self.center_notebook, bg=self.palette["card"])
        self.hints_tab = tk.Frame(self.center_notebook, bg=self.palette["card"])
        self.solution_tab = tk.Frame(self.center_notebook, bg=self.palette["card"])
        self.description_text = make_scrolled_text(self.app.theme_controller, self.description_tab, height=26, editable=False)
        self.hints_text = make_scrolled_text(self.app.theme_controller, self.hints_tab, height=26, editable=False)
        self.solution_text = make_scrolled_text(self.app.theme_controller, self.solution_tab, height=26, editable=False)
        for frame, widget, label in [
            (self.description_tab, self.description_text, "Description"),
            (self.hints_tab, self.hints_text, "Hints"),
            (self.solution_tab, self.solution_text, "Solution"),
        ]:
            frame.configure(bg=self.palette["card"])
            widget.pack(fill="both", expand=True, padx=10, pady=10)
            self.center_notebook.add(frame, text=label)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        self.editor = CodeEditorPanel(
            right,
            self.palette,
            language=self.app.session.selected_language,
            run_callback=self._run_preview,
            submit_callback=self._submit,
            solution_callback=self._view_solution,
            bookmark_callback=self._toggle_bookmark,
            reset_callback=self._reset_template,
            change_callback=self._save_draft,
        )
        self.editor.grid(row=0, column=0, sticky="nsew")
        ToolTip(self.editor.run_button, "Run a structural preview against the sample test cases.")
        ToolTip(self.editor.submit_button, "Store this attempt and get mentor feedback.")
        ToolTip(self.editor.solution_button, "Reveal the optimized reference explanation and code.")

    def refresh(self) -> None:
        self.search_var.set(self.app.practice_query)
        self.difficulty_var.set(self.app.practice_difficulty)
        self._refresh_browser()
        self._refresh_problem_view()

    def _refresh_browser(self) -> None:
        self.app.set_practice_filters(query=self.search_var.get(), difficulty=self.difficulty_var.get())
        tree = self.browser.tree
        self._browser_syncing = True
        try:
            for item in tree.get_children():
                tree.delete(item)
            states = {state.slug: state for state in self.app.mentor_service.get_topic_states(self.app.session.user_id)}
            accessible = self.app.mentor_service.get_accessible_topics(self.app.session.user_id, self.app.session.selected_language)
            practice_rows = self.app.mentor_service.learning_repository.get_practice_rows(self.app.session.user_id)
            attempted_counts: dict[str, int] = {}
            for row in practice_rows:
                attempted_counts[row["topic_slug"]] = attempted_counts.get(row["topic_slug"], 0) + 1
            results = self.app.question_engine.search(
                accessible,
                query=self.search_var.get(),
                difficulty=self.difficulty_var.get(),
            )
            by_topic: dict[str, list[dict]] = {}
            for result in results:
                by_topic.setdefault(result["topic_slug"], []).append(result)
            current_problem = self.app.selected_problem_id
            for group, topics in self.app.course_service.group_map().items():
                group_id = f"group:{group}"
                tree.insert("", tk.END, iid=group_id, text=group, open=True)
                for topic in topics:
                    if topic["slug"] not in accessible:
                        continue
                    visible_problems = by_topic.get(topic["slug"], [])
                    if not visible_problems:
                        continue
                    state = states[topic["slug"]]
                    topic_text = f"{topic['title']}  [{attempted_counts.get(topic['slug'], 0)}/{len(topic['practice'])}]"
                    if state.needs_revision:
                        topic_text += "  Revise"
                    elif state.completed:
                        topic_text += "  Done"
                    topic_id = f"topic:{topic['slug']}"
                    tree.insert(group_id, tk.END, iid=topic_id, text=topic_text, open=topic["slug"] == self.app.selected_topic_slug)
                    for problem in visible_problems:
                        label = f"{problem['title']} ({problem['difficulty']})"
                        tree.insert(topic_id, tk.END, iid=f"problem:{problem['problem_id']}", text=label)

            desired = f"problem:{current_problem}" if current_problem else None
            if desired and tree.exists(desired):
                tree.selection_set(desired)
                tree.focus(desired)
            else:
                first = tree.get_children()
                if first:
                    self._select_first_problem(first[0])
        finally:
            self._browser_syncing = False

    def _select_first_problem(self, node_id: str) -> None:
        tree = self.browser.tree
        children = tree.get_children(node_id)
        for child in children:
            if child.startswith("problem:"):
                problem_id = child.split(":", 1)[1]
                self.app.select_problem(problem_id)
                tree.selection_set(child)
                tree.focus(child)
                return
            self._select_first_problem(child)

    def _on_browser_select(self, _event=None) -> None:
        if self._browser_syncing:
            return
        selection = self.browser.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        if item_id.startswith("problem:"):
            self.app.select_problem(item_id.split(":", 1)[1])
        elif item_id.startswith("topic:"):
            slug = item_id.split(":", 1)[1]
            self.app.select_topic(slug)
        self._refresh_problem_view()

    def _refresh_problem_view(self) -> None:
        if not self.app.selected_problem_id:
            return
        topic, problem = self.app.course_service.get_problem(self.app.selected_problem_id)
        self.breadcrumb_label.configure(text=self.app.course_service.breadcrumb(topic["slug"], problem["id"]))
        self.problem_title.configure(text=problem["title"])
        self.difficulty_chip.configure(text=problem["difficulty"], bg=difficulty_color(self.palette, problem["difficulty"]))

        workspace = self.app.mentor_service.get_problem_workspace(
            self.app.session.user_id,
            topic["slug"],
            problem["id"],
            self.app.session.selected_language,
        )
        description_lines = [
            problem["statement"],
            "",
            "Constraints",
            "\n".join(f"- {item}" for item in problem["constraints"]),
            "",
            "Examples",
        ]
        for example in problem["examples"]:
            description_lines.extend(
                [
                    f"- Input: {example['input']}",
                    f"  Output: {example['output']}",
                    f"  Why: {example['explanation']}",
                    "",
                ]
            )
        description_lines.extend(
            [
                "Optimized Approach",
                problem["optimized_approach"],
            ]
        )
        hints_lines = ["Hints", *[f"- {hint}" for hint in problem["hints"]], "", f"Pattern: {problem['pattern']}"]
        solution_body = "Attempt the problem first, then click 'View Solution' to reveal the optimized approach, pseudo code, complexity, and reference implementation."
        if workspace["viewed_solution"]:
            solution_body = format_solution_content(problem, self.app.session.selected_language)

        set_text(self.description_text, "\n".join(description_lines))
        set_text(self.hints_text, "\n".join(hints_lines))
        set_text(self.solution_text, solution_body)
        self.editor.set_language(self.app.session.selected_language)
        self.editor.set_code(workspace["saved_code"])
        self.editor.set_console(workspace["console"])
        self.editor.set_bookmarked(workspace["bookmarked"])
        status = "Viewed solution" if workspace["viewed_solution"] else ("Attempt score: %.1f" % workspace["score"] if workspace["score"] else "Draft")
        self.editor.set_status(status)

    def _run_preview(self) -> None:
        topic, problem = self.app.course_service.get_problem(self.app.selected_problem_id)
        try:
            evaluation = self.app.mentor_service.preview_practice_attempt(
                self.app.session.user_id,
                topic["slug"],
                problem["id"],
                self.app.session.selected_language,
                self.editor.get_code(),
            )
        except ValueError as exc:
            messagebox.showwarning(APP_NAME, str(exc))
            return
        self.editor.set_console(evaluation["console"])
        self.editor.set_status(f"Preview score: {evaluation['score']:.1f}")
        set_text(self.hints_text, "\n".join(["Hints", *[f"- {hint}" for hint in problem["hints"]], "", "Live Preview Feedback", evaluation["feedback"]]))
        self.center_notebook.select(self.hints_tab)

    def _submit(self) -> None:
        topic, problem = self.app.course_service.get_problem(self.app.selected_problem_id)
        try:
            evaluation = self.app.mentor_service.submit_practice_attempt(
                self.app.session.user_id,
                topic["slug"],
                problem["id"],
                self.app.session.selected_language,
                self.editor.get_code(),
            )
        except ValueError as exc:
            messagebox.showwarning(APP_NAME, str(exc))
            return
        self.editor.set_console(evaluation["console"])
        self.editor.set_status(f"Submitted: {evaluation['score']:.1f}")
        set_text(self.hints_text, "\n".join(["Hints", *[f"- {hint}" for hint in problem["hints"]], "", "Mentor Feedback", evaluation["feedback"]]))
        self.center_notebook.select(self.hints_tab)
        self.shell.refresh_all()
        active_test = self.app.mentor_service.get_active_test(self.app.session.user_id, self.app.session.selected_language)
        if active_test:
            messagebox.showinfo(APP_NAME, "The mentor noticed two study days of work. A test is now waiting in the Tests tab.")

    def _view_solution(self) -> None:
        topic, problem = self.app.course_service.get_problem(self.app.selected_problem_id)
        self.app.mentor_service.mark_solution_viewed(self.app.session.user_id, topic["slug"], problem["id"])
        set_text(self.solution_text, format_solution_content(problem, self.app.session.selected_language))
        self.center_notebook.select(self.solution_tab)
        self.editor.set_status("Viewed solution")

    def _toggle_bookmark(self) -> None:
        topic, problem = self.app.course_service.get_problem(self.app.selected_problem_id)
        bookmarked = self.app.mentor_service.toggle_bookmark(self.app.session.user_id, topic["slug"], problem["id"])
        self.editor.set_bookmarked(bookmarked)

    def _reset_template(self) -> None:
        _topic, problem = self.app.course_service.get_problem(self.app.selected_problem_id)
        self.editor.set_code(problem["starter_code"][self.app.session.selected_language])
        self.editor.set_status("Template restored")

    def _save_draft(self) -> None:
        if not self.app.selected_problem_id:
            return
        topic, problem = self.app.course_service.get_problem(self.app.selected_problem_id)
        self.app.mentor_service.save_practice_draft(
            self.app.session.user_id,
            topic["slug"],
            problem["id"],
            self.editor.get_code(),
        )

    def _open_random_problem(self) -> None:
        completed = self.app.mentor_service.get_completed_topics(self.app.session.user_id)
        if not completed:
            messagebox.showinfo(APP_NAME, "Practice Mode opens after you complete at least one topic.")
            return
        pick = self.app.question_engine.random_problem(completed, difficulty=self.difficulty_var.get())
        if not pick:
            messagebox.showinfo(APP_NAME, "No completed-topic problem matches the current difficulty filter.")
            return
        self.app.select_problem(pick["problem_id"])
        self._refresh_browser()
        self._refresh_problem_view()


class TestsPage(tk.Frame):
    def __init__(self, parent: tk.Widget, shell: MainShell) -> None:
        super().__init__(parent, bg=shell.palette["bg"])
        self.shell = shell
        self.app = shell.app
        self.palette = shell.palette
        self.answer_widgets: dict[str, object] = {}
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        header = tk.Frame(self, bg=self.palette["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(header, text="Mentor Tests", bg=self.palette["bg"], fg=self.palette["text"], font=(FONT_FAMILY, 26, "bold")).pack(anchor="w")
        tk.Label(header, text="Tests are triggered automatically after every two distinct study days.", bg=self.palette["bg"], fg=self.palette["muted"], font=(FONT_FAMILY, 11)).pack(anchor="w", pady=(6, 0))
        self.body = ScrollableFrame(self, self.palette)
        self.body.grid(row=1, column=0, sticky="nsew")

    def refresh(self) -> None:
        clear_children(self.body.inner)
        self.answer_widgets.clear()
        active_test = self.app.mentor_service.get_active_test(self.app.session.user_id, self.app.session.selected_language)
        if active_test:
            self._render_active_test(active_test)
        else:
            self._render_history()

    def _render_active_test(self, active_test) -> None:
        topic_titles = [self.app.course_service.get_topic(slug)["title"] for slug in active_test.topics]
        card = tk.Frame(self.body.inner, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        card.pack(fill="x", pady=(0, 12))
        tk.Label(card, text="Mandatory Mentor Assessment", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 17, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        tk.Label(card, text=f"Coverage: {', '.join(topic_titles)}", bg=self.palette["card"], fg=self.palette["muted"], font=(FONT_FAMILY, 10)).pack(anchor="w", padx=16, pady=(0, 4))
        tk.Label(card, text="Pass score: 70 or higher" if active_test.status != "revision_required" else "Revision required before retrying", bg=self.palette["card"], fg=self.palette["warning"], font=(FONT_FAMILY, 10, "bold")).pack(anchor="w", padx=16, pady=(0, 14))

        unresolved = [
            state.title
            for state in self.app.mentor_service.get_topic_states(self.app.session.user_id)
            if state.needs_revision and state.slug in active_test.topics
        ]
        if unresolved:
            box = tk.Frame(self.body.inner, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
            box.pack(fill="x", pady=(0, 12))
            tk.Label(box, text="Revision Lock", bg=self.palette["card"], fg=self.palette["danger"], font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
            tk.Label(box, text="Revisit these topics before retaking: " + ", ".join(unresolved), bg=self.palette["card"], fg=self.palette["text"], wraplength=980, justify="left", font=(FONT_FAMILY, 10)).pack(anchor="w", padx=16, pady=(0, 14))

        for number, question in enumerate(active_test.questions, start=1):
            qcard = tk.Frame(self.body.inner, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
            qcard.pack(fill="x", pady=(0, 12))
            title = question["title"] if question["type"] == "coding" else f"{self.app.course_service.get_topic(question['topic_slug'])['title']} MCQ"
            tk.Label(qcard, text=f"Q{number}. {title}", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 13, "bold")).pack(anchor="w", padx=16, pady=(14, 8))
            tk.Label(qcard, text=question["prompt"], bg=self.palette["card"], fg=self.palette["text"], justify="left", wraplength=980, font=(FONT_FAMILY, 10)).pack(anchor="w", padx=16, pady=(0, 12))
            if question["type"] == "mcq":
                choice = tk.StringVar(value="")
                self.answer_widgets[question["id"]] = choice
                for index, option in enumerate(question["options"]):
                    radio = tk.Radiobutton(
                        qcard,
                        text=option,
                        variable=choice,
                        value=str(index),
                        bg=self.palette["card"],
                        fg=self.palette["text"],
                        activebackground=self.palette["card"],
                        activeforeground=self.palette["text"],
                        selectcolor=self.palette["panel"],
                        justify="left",
                        wraplength=940,
                    )
                    radio.pack(anchor="w", padx=22, pady=4)
            else:
                lines = ["Examples"] + [f"- Input: {case['input']} | Output: {case['output']}" for case in question["test_cases"]]
                tk.Label(qcard, text="\n".join(lines), bg=self.palette["card"], fg=self.palette["muted"], justify="left", wraplength=980, font=(FONT_FAMILY, 10)).pack(anchor="w", padx=16, pady=(0, 8))
                editor = make_scrolled_text(self.app.theme_controller, qcard, height=10, editable=True)
                editor.pack(fill="x", padx=16, pady=(0, 16))
                self.answer_widgets[question["id"]] = editor

        submit = make_button(self.body.inner, "Submit Mentor Test", lambda: self._submit(active_test.test_id), self.palette, kind="primary")
        submit.pack(anchor="e", pady=(4, 14))
        if unresolved:
            submit.configure(state="disabled")

    def _render_history(self) -> None:
        card = tk.Frame(self.body.inner, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        card.pack(fill="both", expand=True)
        tk.Label(card, text="No Pending Mentor Test", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 18, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        tk.Label(card, text="History stays here, and the next assessment appears automatically after two distinct study days.", bg=self.palette["card"], fg=self.palette["muted"], font=(FONT_FAMILY, 10)).pack(anchor="w", padx=16, pady=(0, 12))
        tree = ttk.Treeview(card, columns=("id", "status", "score", "topics", "attempts"), show="headings", height=12)
        for column, label, width in [("id", "Test", 80), ("status", "Status", 180), ("score", "Score", 100), ("topics", "Topics", 560), ("attempts", "Attempts", 100)]:
            tree.heading(column, text=label)
            tree.column(column, width=width, anchor="w")
        tree.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        for test in self.app.mentor_service.get_test_history(self.app.session.user_id):
            topics = ", ".join(self.app.course_service.get_topic(slug)["title"] for slug in test.topics)
            tree.insert("", tk.END, values=(test.test_id, test.status.replace("_", " ").title(), "-" if test.score is None else f"{test.score:.1f}", topics, test.attempts))

    def _submit(self, test_id: int) -> None:
        answers = []
        for question_id, widget in self.answer_widgets.items():
            if isinstance(widget, tk.StringVar):
                answers.append({"id": question_id, "value": widget.get()})
            else:
                answers.append({"id": question_id, "value": widget.get("1.0", tk.END).strip()})
        try:
            result = self.app.mentor_service.submit_test(self.app.session.user_id, test_id, self.app.session.selected_language, answers)
        except ValueError as exc:
            messagebox.showwarning(APP_NAME, str(exc))
            return
        self.shell.refresh_all()
        if result["passed"]:
            messagebox.showinfo(APP_NAME, f"Passed with {result['score']:.1f}. The next topic gate is now open.")
        else:
            topics = ", ".join(self.app.course_service.get_topic(slug)["title"] for slug in result["topics"])
            messagebox.showwarning(APP_NAME, f"Score: {result['score']:.1f}. Revise these topics before retrying: {topics}")


class ProfilePage(tk.Frame):
    def __init__(self, parent: tk.Widget, shell: MainShell) -> None:
        super().__init__(parent, bg=shell.palette["bg"])
        self.shell = shell
        self.app = shell.app
        self.palette = shell.palette
        self._build()

    def _card(self, parent: tk.Widget, title: str) -> tuple[tk.Frame, tk.Label]:
        card = tk.Frame(parent, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        tk.Label(card, text=title, bg=self.palette["card"], fg=self.palette["muted"], font=(FONT_FAMILY, 10, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        value = tk.Label(card, text="-", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 18, "bold"), wraplength=280, justify="left")
        value.pack(anchor="w", padx=16, pady=(0, 14))
        return card, value

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        tk.Label(self, text="Profile", bg=self.palette["bg"], fg=self.palette["text"], font=(FONT_FAMILY, 26, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 14))
        cards = tk.Frame(self, bg=self.palette["bg"])
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        cards.columnconfigure((0, 1, 2, 3), weight=1)
        c1, self.user_value = self._card(cards, "Learner")
        c2, self.language_value = self._card(cards, "Language")
        c3, self.avg_value = self._card(cards, "Average Practice Score")
        c4, self.attempts_value = self._card(cards, "Practice Attempts")
        for idx, card in enumerate((c1, c2, c3, c4)):
            card.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 8, 0))

        lower = tk.Frame(self, bg=self.palette["bg"])
        lower.grid(row=2, column=0, sticky="nsew")
        lower.columnconfigure(0, weight=2)
        lower.columnconfigure(1, weight=3)
        lower.rowconfigure(0, weight=1)

        bookmarks = tk.Frame(lower, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        bookmarks.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        bookmarks.columnconfigure(0, weight=1)
        bookmarks.rowconfigure(1, weight=1)
        tk.Label(bookmarks, text="Bookmarks", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 14, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        self.bookmark_tree = ttk.Treeview(bookmarks, columns=("title", "topic", "difficulty"), show="headings", height=14)
        self.bookmark_tree.heading("title", text="Problem")
        self.bookmark_tree.heading("topic", text="Topic")
        self.bookmark_tree.heading("difficulty", text="Difficulty")
        self.bookmark_tree.column("title", width=260, anchor="w")
        self.bookmark_tree.column("topic", width=220, anchor="w")
        self.bookmark_tree.column("difficulty", width=100, anchor="center")
        self.bookmark_tree.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        self.bookmark_tree.bind("<Double-1>", lambda _event: self._open_bookmark())
        make_button(bookmarks, "Open In Practice", self._open_bookmark, self.palette, kind="primary").grid(row=2, column=0, sticky="e", padx=16, pady=(0, 16))

        roadmap = tk.Frame(lower, bg=self.palette["card"], highlightthickness=1, highlightbackground=self.palette["border"])
        roadmap.grid(row=0, column=1, sticky="nsew")
        roadmap.columnconfigure(0, weight=1)
        roadmap.rowconfigure(1, weight=1)
        tk.Label(roadmap, text="Beginner Roadmap", bg=self.palette["card"], fg=self.palette["text"], font=(FONT_FAMILY, 14, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        self.roadmap_tree = ttk.Treeview(roadmap, columns=("focus", "count"), show="headings", height=12)
        self.roadmap_tree.heading("focus", text="Focus")
        self.roadmap_tree.heading("count", text="Problems")
        self.roadmap_tree.column("focus", width=470, anchor="w")
        self.roadmap_tree.column("count", width=100, anchor="center")
        self.roadmap_tree.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        footer = tk.Frame(roadmap, bg=self.palette["card"])
        footer.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.revision_label = tk.Label(footer, text="", bg=self.palette["card"], fg=self.palette["warning"], font=(FONT_FAMILY, 10), justify="left", wraplength=540)
        self.revision_label.pack(side="left")
        make_button(footer, "Replay Tutorial", self.app.open_tutorial, self.palette).pack(side="right")

    def refresh(self) -> None:
        profile = self.app.mentor_service.profile_snapshot(self.app.session.user_id, self.app.session.selected_language)
        self.user_value.configure(text=self.app.session.username)
        self.language_value.configure(text=self.app.session.selected_language)
        self.avg_value.configure(text=f"{profile['average_practice_score']:.1f}")
        self.attempts_value.configure(text=str(profile["practice_attempts"]))

        for item in self.bookmark_tree.get_children():
            self.bookmark_tree.delete(item)
        for bookmark in profile["bookmarks"]:
            self.bookmark_tree.insert("", tk.END, iid=bookmark["problem_id"], values=(bookmark["title"], bookmark["topic_title"], bookmark["difficulty"]))

        for item in self.roadmap_tree.get_children():
            self.roadmap_tree.delete(item)
        for row in profile["recommended_path"]:
            self.roadmap_tree.insert("", tk.END, values=(f"{row['step']}. {row['title']} - {row['focus']}", row["problem_count"]))

        if profile["revision_topics"]:
            self.revision_label.configure(text="Revision watchlist: " + ", ".join(profile["revision_topics"]))
        else:
            self.revision_label.configure(text="Revision watchlist is clear right now.")

    def _open_bookmark(self) -> None:
        selection = self.bookmark_tree.selection()
        if not selection:
            return
        problem_id = selection[0]
        self.app.select_problem(problem_id)
        self.shell.show_page("practice")


def launch_app() -> None:
    database = DatabaseManager()
    database.initialize()
    course_service = CourseService()
    question_engine = QuestionEngineService(course_service)
    user_repository = UserRepository(database)
    learning_repository = LearningRepository(database)
    auth_service = AuthService(user_repository, learning_repository, course_service)
    mentor_service = MentorService(learning_repository, course_service, question_engine)
    app = DsaMentorApp(auth_service, mentor_service, course_service, question_engine)
    app.mainloop()
