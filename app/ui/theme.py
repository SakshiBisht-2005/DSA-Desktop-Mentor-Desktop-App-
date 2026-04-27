from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.config import FONT_FAMILY


PALETTES = {
    "dark": {
        "bg": "#0f1218",
        "panel": "#161b24",
        "card": "#1d2430",
        "card_alt": "#242c3b",
        "border": "#2d3647",
        "text": "#eef3fb",
        "muted": "#95a3ba",
        "accent": "#43b88c",
        "accent_soft": "#2b7c61",
        "warning": "#f5a524",
        "danger": "#ef6a6a",
        "success": "#44c48c",
        "editor": "#0b0f15",
    },
    "light": {
        "bg": "#edf2f8",
        "panel": "#ffffff",
        "card": "#f8fbff",
        "card_alt": "#eef4fb",
        "border": "#d5ddea",
        "text": "#132034",
        "muted": "#5b6980",
        "accent": "#0d8b68",
        "accent_soft": "#b9e7d8",
        "warning": "#d97706",
        "danger": "#d64545",
        "success": "#1f8f5f",
        "editor": "#ffffff",
    },
}


class ThemeController:
    def __init__(self, root: tk.Tk, mode: str) -> None:
        self.root = root
        self.mode = mode if mode in PALETTES else "dark"
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.apply()

    @property
    def palette(self) -> dict[str, str]:
        return PALETTES[self.mode]

    def set_mode(self, mode: str) -> None:
        self.mode = mode if mode in PALETTES else "dark"
        self.apply()

    def apply(self) -> None:
        colors = self.palette
        self.root.configure(bg=colors["bg"])
        self.style.configure(
            ".",
            font=(FONT_FAMILY, 10),
            background=colors["panel"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TLabel",
            background=colors["panel"],
            foreground=colors["text"],
        )
        self.style.configure(
            "TButton",
            padding=8,
            borderwidth=0,
            relief="flat",
            foreground=colors["text"],
            background=colors["card_alt"],
        )
        self.style.map(
            "TButton",
            background=[("active", colors["accent_soft"])],
            foreground=[("active", colors["text"])],
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=colors["card"],
            background=colors["card"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            arrowcolor=colors["text"],
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["card"])],
            foreground=[("readonly", colors["text"])],
            selectbackground=[("readonly", colors["card"])],
            selectforeground=[("readonly", colors["text"])],
        )
        self.style.configure(
            "Treeview",
            background=colors["card"],
            fieldbackground=colors["card"],
            foreground=colors["text"],
            bordercolor=colors["border"],
            rowheight=30,
        )
        self.style.map(
            "Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["panel"])],
        )
        self.style.configure(
            "Treeview.Heading",
            background=colors["card_alt"],
            foreground=colors["text"],
            relief="flat",
        )
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor=colors["card_alt"],
            background=colors["accent"],
            bordercolor=colors["border"],
            lightcolor=colors["accent"],
            darkcolor=colors["accent"],
        )
        self.style.configure(
            "TNotebook",
            background=colors["panel"],
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            background=colors["card_alt"],
            foreground=colors["text"],
            padding=(14, 8),
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", colors["accent_soft"])],
            foreground=[("selected", colors["text"])],
        )

    def style_text_widget(self, widget: tk.Text, *, editable: bool = True) -> None:
        colors = self.palette
        widget.configure(
            bg=colors["editor"],
            fg=colors["text"],
            insertbackground=colors["text"],
            selectbackground=colors["accent"],
            selectforeground=colors["panel"],
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
            padx=12,
            pady=12,
            font=(FONT_FAMILY, 10),
            wrap="word",
        )
        if not editable:
            widget.configure(state="disabled")

    def style_listbox(self, widget: tk.Listbox) -> None:
        colors = self.palette
        widget.configure(
            bg=colors["card"],
            fg=colors["text"],
            selectbackground=colors["accent"],
            selectforeground=colors["panel"],
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"],
            font=(FONT_FAMILY, 10),
        )

