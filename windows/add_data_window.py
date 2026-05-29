import tkinter as tk
from tkinter import ttk

from db import db_add
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

        book_tab = AddBookTab(notebook, app)
        notebook.add(book_tab, text="Book")

        # =========================
        # AUTHOR TAB
        # =========================

        author_tab = AuthorTab(notebook, app)
        notebook.add(author_tab, text="Author")

        # =========================
        # SERIES TAB
        # =========================

        series_tab = SeriesTab(notebook, app)
        notebook.add(series_tab, text="Series")

        # =========================
        # Genre TAB
        # =========================

        genre_tab = GenreTab(notebook, app)
        notebook.add(genre_tab, text="Genre")
