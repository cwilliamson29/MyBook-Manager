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
        self.app = app

        self.title("Add Data")
        self.geometry("500x400")

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

        # notebook.bind('<<NotebookTabChanged>>', self.on_change())

    def refresh_book_tab_authors(self):
        self.book_tab.refresh_authors()

    def refresh_book_tab_genre(self):
        self.book_tab.refresh_genres()

    def refresh_series_tab_authors(self):
        self.series_tab.refresh_authors()