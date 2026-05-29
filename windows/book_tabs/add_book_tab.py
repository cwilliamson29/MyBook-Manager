import tkinter as tk

from db import db_get


class AddBookTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.authors = db_get.get_authors()
        self.genres = db_get.get_genres()

        # Book Title
        tk.Label(self, text="Book Title:").grid(row=0, column=0, sticky="e")
        self.title_entry = tk.Entry(self, width=20)
        self.title_entry.grid(row=0, column=1, sticky="w")

        # Authors
        tk.Label(self, text="Select Author:").grid(row=1, column=0, sticky="e")
        self.selected_author = tk.StringVar()
        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }
        self.dropdown = tk.OptionMenu(
            self,
            self.selected_author,
            *self.author_map.keys()
        )
        self.dropdown.grid(row=1, column=1, sticky="w")
        self.author_var = tk.StringVar()
        self.selected_author.trace_add("write", self.author_selected)

        self.series_var = tk.StringVar()

        self.series_label = tk.Label(self, text="Select Series:")

        self.series_dropdown = tk.OptionMenu(
            self,
            self.series_var,
            ""
        )

        # Number in series
        self.num_in_series = tk.Label(self, text="Book Number:")

        self.num_in_series_entry = tk.Entry(self, width=20)

        # Hide initially
        self.series_dropdown.grid_forget()
        self.series_label.grid_forget()
        self.num_in_series.grid_forget()

        # Rating
        tk.Label(self, text="Rating").grid(row=4, column=0, sticky="e")
        self.rating = tk.Entry(self, width=20)
        self.rating.grid(row=4, column=1, sticky="w")

        # Genres
        tk.Label(self, text="Select Genre:").grid(row=5, column=0, sticky="e")
        self.selected_genre = tk.StringVar()
        self.genre_map = {
            f"{title}": genre_id
            for genre_id, title in self.genres
        }
        self.genre_dropdown = tk.OptionMenu(
            self,
            self.selected_genre,
            *self.genre_map.keys()
        )
        self.genre_dropdown.grid(row=5, column=1, sticky="w")

        # ISBN
        tk.Label(self, text="ISBN:").grid(row=6, column=0, sticky="e")
        self.isbn_entry = tk.Entry(self, width=20)
        self.isbn_entry.grid(row=6, column=1, sticky="w")

        # NLS Order
        tk.Label(self, text="NLS Order:").grid(row=7, column=0, sticky="e")
        self.nls_order = tk.Entry(self, width=20)
        self.nls_order.grid(row=7, column=1, sticky="w")

        tk.Button(
            self,
            text="Add Author",
            command=self.add_author
        ).grid(row=8, column=1)

    def author_selected(self, *args):

        selected = self.selected_author.get()

        if not selected:
            return

        author_id = self.author_map[selected]

        # Get series from database
        series = db_get.get_series_by_author(author_id)

        # Clear existing menu
        menu = self.series_dropdown["menu"]
        menu.delete(0, "end")

        self.series_map = {}

        # Add new options
        for series_id, title in series:
            self.series_map[title] = series_id

            menu.add_command(
                label=title,
                command=lambda value=title:
                self.series_var.set(value)
            )

        if not self.series_map:
            self.series_dropdown.grid_forget()
            self.series_label.grid_forget()
            self.num_in_series.grid_forget()
            self.num_in_series_entry.grid_forget()
        else:
            # Show dropdown only AFTER author selected
            self.series_label.grid(row=2, column=0, sticky="e")
            self.series_dropdown.grid(row=2, column=1, sticky="w")
            self.num_in_series.grid(row=3, column=0, sticky="e")
            self.num_in_series_entry.grid(row=3, column=1, sticky="w")

        # Set default value
        if series:
            self.series_var.set(series[0][1])


    def add_author(self):
        first = self.first.get().strip()
        last = self.last.get().strip()

        if not first or not last:
            return

        # db_add.add_author(first, last)

        # self.first.delete(0, tk.END)
        # self.last.delete(0, tk.END)