import tkinter as tk
import customtkinter as ctk

from db import db_add, db_get
from windows.book_tabs.add_author_tab import AuthorTab
from windows.book_tabs.add_book_tab import AddBookTab
from windows.book_tabs.add_genre_tab import GenreTab
from windows.book_tabs.add_series_tab import SeriesTab
from windows.book_tabs.add_topic_tab import TopicsTab


class AddDataWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app.root)

        self.withdraw()

        self.app = app

        self.title("Add New Data")

        self.center_on_parent(app.root, 520, 700)

        self.deiconify()
        # =========================
        # TABVIEW
        # =========================

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("Book")
        self.tabview.add("Author")
        self.tabview.add("Series")
        self.tabview.add("Genre")
        self.tabview.add("Topics")

        # =========================
        # BOOK TAB
        # =========================

        self.book_tab = AddBookTab(self.tabview.tab("Book"), self.app)
        self.book_tab.pack(fill="both", expand=True)

        # =========================
        # AUTHOR TAB
        # =========================

        self.author_tab = AuthorTab(self.tabview.tab("Author"), self.app, self)
        self.author_tab.pack(fill="both", expand=True)

        # =========================
        # SERIES TAB
        # =========================

        self.series_tab = SeriesTab(self.tabview.tab("Series"), self.app)
        self.series_tab.pack(fill="both", expand=True)

        # =========================
        # Genre TAB
        # =========================

        genre_tab = GenreTab(self.tabview.tab("Genre"), self.app, self)
        genre_tab.pack(fill="both", expand=True)

        # =========================
        # Topics TAB
        # =========================

        topics_tab = TopicsTab(self.tabview.tab("Topics"), self.app, self)
        topics_tab.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def refresh_book_tab_authors(self):
        self.book_tab.refresh_authors()

    def refresh_book_tab_genre(self):
        self.book_tab.refresh_genres()

    def refresh_series_tab_authors(self):
        self.series_tab.refresh_authors()

    def refresh_book_tab_topics(self):
        self.book_tab.refresh_topics()

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