from __future__ import annotations

import re
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from app.core.config import CODE_FONT_FAMILY, FONT_FAMILY
from app.services.question_engine import LANGUAGE_KEYWORDS


class CodeEditorPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        palette: dict[str, str],
        *,
        language: str,
        run_callback,
        submit_callback,
        solution_callback,
        bookmark_callback,
        reset_callback,
        change_callback=None,
    ) -> None:
        super().__init__(parent, bg=palette["card"], highlightthickness=1, highlightbackground=palette["border"])
        self.palette = palette
        self.language = language
        self.run_callback = run_callback
        self.submit_callback = submit_callback
        self.solution_callback = solution_callback
        self.bookmark_callback = bookmark_callback
        self.reset_callback = reset_callback
        self.change_callback = change_callback
        self._autosave_after_id: str | None = None
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(4, weight=0)

        header = tk.Frame(self, bg=self.palette["card"])
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        header.columnconfigure(0, weight=1)
        self.title_label = tk.Label(
            header,
            text=f"{self.language} Editor",
            bg=self.palette["card"],
            fg=self.palette["text"],
            font=(FONT_FAMILY, 13, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.status_label = tk.Label(
            header,
            text="Draft",
            bg=self.palette["card"],
            fg=self.palette["muted"],
            font=(FONT_FAMILY, 10),
        )
        self.status_label.grid(row=0, column=1, sticky="e")

        button_row = tk.Frame(self, bg=self.palette["card"])
        button_row.grid(row=1, column=0, sticky="ew", padx=16)
        self.bookmark_button = self._button(button_row, "Bookmark", self.bookmark_callback)
        self.bookmark_button.pack(side="left", padx=(0, 8))
        self.reset_button = self._button(button_row, "Reset", self.reset_callback)
        self.reset_button.pack(side="left", padx=(0, 8))
        self.solution_button = self._button(button_row, "View Solution", self.solution_callback)
        self.solution_button.pack(side="left", padx=(0, 8))
        self.run_button = self._button(button_row, "Run Code", self.run_callback)
        self.run_button.pack(side="right", padx=(8, 0))
        self.submit_button = self._button(button_row, "Submit", self.submit_callback, accent=True)
        self.submit_button.pack(side="right")

        self.code = ScrolledText(
            self,
            wrap="none",
            font=(CODE_FONT_FAMILY, 10),
            bg=self.palette["editor"],
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.palette["border"],
            highlightcolor=self.palette["accent"],
            padx=12,
            pady=12,
            undo=True,
        )
        self.code.grid(row=2, column=0, sticky="nsew", padx=16, pady=(12, 10))

        console_label = tk.Label(
            self,
            text="Output Console",
            bg=self.palette["card"],
            fg=self.palette["muted"],
            font=(FONT_FAMILY, 10, "bold"),
        )
        console_label.grid(row=3, column=0, sticky="w", padx=16)

        self.console = ScrolledText(
            self,
            wrap="word",
            height=8,
            font=(CODE_FONT_FAMILY, 9),
            bg=self.palette["panel"],
            fg=self.palette["muted"],
            insertbackground=self.palette["text"],
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.palette["border"],
            padx=12,
            pady=12,
        )
        self.console.grid(row=4, column=0, sticky="ew", padx=16, pady=(8, 16))
        self.console.configure(state="disabled")

        self.code.tag_configure("keyword", foreground="#ff8a5b")
        self.code.tag_configure("builtin", foreground="#5ec4ff")
        self.code.tag_configure("comment", foreground="#7d8ba5")
        self.code.tag_configure("string", foreground="#f5d061")
        self.code.tag_configure("number", foreground="#c68cff")
        self.code.bind("<KeyRelease>", self._on_key_release)

    def _button(self, parent: tk.Widget, text: str, command, accent: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.palette["accent"] if accent else self.palette["card_alt"],
            fg=self.palette["panel"] if accent else self.palette["text"],
            activebackground=self.palette["accent_soft"],
            activeforeground=self.palette["text"],
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=8,
            cursor="hand2",
            font=(FONT_FAMILY, 10, "bold"),
        )

    def set_language(self, language: str) -> None:
        self.language = language
        self.title_label.configure(text=f"{language} Editor")
        self.highlight_syntax()

    def set_code(self, code: str) -> None:
        self.code.delete("1.0", tk.END)
        self.code.insert("1.0", code)
        self.highlight_syntax()

    def get_code(self) -> str:
        return self.code.get("1.0", tk.END).rstrip()

    def set_console(self, text: str) -> None:
        self.console.configure(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.insert("1.0", text)
        self.console.configure(state="disabled")

    def set_bookmarked(self, bookmarked: bool) -> None:
        self.bookmark_button.configure(text="Remove Bookmark" if bookmarked else "Bookmark")

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def highlight_syntax(self) -> None:
        content = self.get_code()
        self.code.tag_remove("keyword", "1.0", tk.END)
        self.code.tag_remove("builtin", "1.0", tk.END)
        self.code.tag_remove("comment", "1.0", tk.END)
        self.code.tag_remove("string", "1.0", tk.END)
        self.code.tag_remove("number", "1.0", tk.END)
        profile = LANGUAGE_KEYWORDS[self.language]
        for token in profile["keywords"]:
            self._highlight_token(token, "keyword")
        for token in profile["builtins"]:
            self._highlight_token(token, "builtin")
        comment_prefix = re.escape(profile["comments"])
        self._highlight_pattern(rf"{comment_prefix}.*$", "comment")
        self._highlight_pattern(r"'[^'\n]*'|\"[^\"\n]*\"", "string")
        self._highlight_pattern(r"\b\d+\b", "number")
        if content:
            self.set_status("Draft saved locally")

    def _highlight_token(self, token: str, tag: str) -> None:
        pattern = rf"\b{re.escape(token)}\b"
        self._highlight_pattern(pattern, tag)

    def _highlight_pattern(self, pattern: str, tag: str) -> None:
        content = self.get_code()
        for match in re.finditer(pattern, content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.code.tag_add(tag, start, end)

    def _on_key_release(self, _event=None) -> None:
        self.highlight_syntax()
        if not self.change_callback:
            return
        if self._autosave_after_id:
            self.after_cancel(self._autosave_after_id)
        self._autosave_after_id = self.after(600, self._flush_change)

    def _flush_change(self) -> None:
        self._autosave_after_id = None
        if self.change_callback:
            self.change_callback()
