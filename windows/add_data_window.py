import tkinter as tk
from tkinter import ttk

from db import db_add, db_get
from windows.book_tabs.add_author_tab import AuthorTab
from windows.book_tabs.add_book_tab import AddBookTab
from windows.book_tabs.add_genre_tab import GenreTab
from windows.book_tabs.add_series_tab import SeriesTab


class AddDataWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)

        self.withdraw()

        self.app = app

        self.title("Add")

        self.center_on_parent(app.root,500, 480)

        self.deiconify()
        # =========================
        # NOTEBOOK (TABS)
        # =========================

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # =========================
        # BOOK TAB
        # =========================

        self.book_tab = AddBookTab(notebook, self.app)
        notebook.add(self.book_tab, text="Book")

        # =========================
        # AUTHOR TAB
        # =========================

        self.author_tab = AuthorTab(notebook, self.app, self)
        notebook.add(self.author_tab, text="Author")

        # =========================
        # SERIES TAB
        # =========================

        self.series_tab = SeriesTab(notebook, self.app)
        notebook.add(self.series_tab, text="Series")

        # =========================
        # Genre TAB
        # =========================

        genre_tab = GenreTab(notebook, self.app, self)
        notebook.add(genre_tab, text="Genre")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_book_tab_authors(self):
        self.book_tab.refresh_authors()

    def refresh_book_tab_genre(self):
        self.book_tab.refresh_genres()

    def refresh_series_tab_authors(self):
        self.series_tab.refresh_authors()

    def on_close(self):
        # Reset reference in main app
        self.app.add_window = None
        self.destroy()

    def center_on_parent(self, parent, width, height):
        parent.update_idletasks()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")