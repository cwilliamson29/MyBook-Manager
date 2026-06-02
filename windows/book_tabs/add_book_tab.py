import tkinter as tk
import customtkinter as ctk
from CTkColorPicker import *

from db import db_get, db_add


class AddBookTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.parent = parent

        self.authors = db_get.get_authors()
        self.genres = db_get.get_genres_titles()
        self.series_map = {}


        # Book Title
        tk.Label(self, text="Book Title:").grid(row=0, column=0, sticky="e")
        self.title_entry = ctk.CTkEntry(self, width=200)
        self.title_entry.grid(row=0, column=1, sticky="w", pady=2)

        # Authors
        tk.Label(self, text="Select Author:").grid(row=1, column=0, sticky="e", pady=2)
        self.selected_author = tk.StringVar()
        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }

        self.author_dropdown = ctk.CTkComboBox(
            self,
            values=list(self.author_map.keys()),
            variable=self.selected_author
        )
        self.author_dropdown.grid(row=1, column=1, sticky="w", pady=2)
        self.author_var = tk.StringVar()
        self.selected_author.trace_add("write", self.author_selected)

        # Series
        self.selected_series = tk.StringVar()

        self.series_label = tk.Label(self, text="Select Series:")

        # self.series_dropdown = tk.OptionMenu(
        #     self,
        #     self.series_var,
        #     ""
        # )
        self.series_dropdown = ctk.CTkComboBox(
            self,
            values=list(""),
            variable=self.selected_series
        )

        # Number in series
        self.num_in_series = tk.Label(self, text="Book Number:")

        self.num_in_series_entry = ctk.CTkEntry(self, width=200)

        # Hide initially
        self.series_dropdown.grid_forget()
        self.series_label.grid_forget()
        self.num_in_series.grid_forget()

        # Rating
        tk.Label(self, text="Rating").grid(row=4, column=0, sticky="e", pady=2)
        self.rating_entry = ctk.CTkEntry(self, width=200)
        self.rating_entry.grid(row=4, column=1, sticky="w", pady=2)

        # Genres
        tk.Label(self, text="Select Genre:").grid(row=5, column=0, sticky="e", pady=2)
        self.selected_genre = tk.StringVar()
        self.genre_map = {
            f"{title}": genre_id
            for genre_id, title in self.genres
        }
        self.genre_dropdown = ctk.CTkComboBox(
            self,
            values=list(self.genre_map.keys()),
            variable=self.selected_genre
        )
        self.genre_dropdown.grid(row=5, column=1, sticky="w", pady=2)

        # ISBN
        tk.Label(self, text="ISBN:").grid(row=6, column=0, sticky="e", pady=2)
        self.isbn_entry = ctk.CTkEntry(self, width=200)
        self.isbn_entry.grid(row=6, column=1, sticky="w", pady=2)

        # NLS Order
        tk.Label(self, text="NLS Order:").grid(row=7, column=0, sticky="e", pady=2)
        self.nls_order_entry = ctk.CTkEntry(self, width=200)
        self.nls_order_entry.grid(row=7, column=1, sticky="w", pady=2)

        self.error_label = tk.Label(self, text="", fg="red")
        self.success_label = tk.Label(self, text="Book Successfully Added!", fg="green")

        ctk.CTkButton(
            self,
            text="Add Book",
            command=self.add_book
        ).grid(row=9, column=1, pady=2)



    def author_selected(self, *args):

        selected = self.selected_author.get()

        if not selected:
            return

        author_id = self.author_map[selected]

        # Get series from database
        series = db_get.get_series_by_author(author_id)

        smap = {
            f"{title}": series_id
            for series_id, title in series
        }
        self.series_map = smap
        self.series_dropdown.configure(values=list(self.series_map.keys()))

        if not self.series_map:
            self.series_dropdown.grid_forget()
            self.series_label.grid_forget()
            self.num_in_series.grid_forget()
            self.num_in_series_entry.grid_forget()
        else:
            # Show dropdown only AFTER author selected
            self.series_label.grid(row=2, column=0, sticky="e", pady=2)
            self.series_dropdown.grid(row=2, column=1, sticky="w", pady=2)
            self.num_in_series.grid(row=3, column=0, sticky="e", pady=2)
            self.num_in_series_entry.grid(row=3, column=1, sticky="w", pady=2)

        # Set default value
        if series:
            self.selected_series.set(series[0][1])


    def add_book(self):
        title = self.title_entry.get().strip()
        author_name = self.selected_author.get()
        series = self.selected_series.get()

        if not series:
            series_id = None
        else:
            series_id = self.series_map[series]

        book_num = self.num_in_series_entry.get().strip()
        rating = self.rating_entry.get().strip()
        genre = self.selected_genre.get()

        if not genre:
            genre_id = None
        else:
            genre_id = self.genre_map[genre]

        isbn = self.isbn_entry.get().strip()
        nls = self.nls_order_entry.get().strip()

        if not title or not author_name or not genre:
            if not title:
                self.title_entry.configure(border_color="red")
            if not author_name:
                self.author_dropdown.configure(border_color="red")
            if not genre:
                self.genre_dropdown.configure(border_color="red")

            self.error_label.config(text="Title, author, and Genre required")
            self.error_label.grid(row=8, column=1)
            return

        author_id = self.author_map[author_name]

        data = (title, author_id, series_id, book_num, rating, genre_id, isbn, nls)
        db_attempt = db_add.add_book(data)
        if db_attempt == "success":
            self.title_entry.delete(0, tk.END)
            self.num_in_series_entry.delete(0, tk.END)
            self.rating_entry.delete(0, tk.END)
            self.isbn_entry.delete(0, tk.END)
            self.nls_order_entry.delete(0, tk.END)
            self.selected_author.set("")
            self.selected_genre.set("")
            self.selected_series.set("")

            self.series_dropdown.grid_forget()
            self.series_label.grid_forget()
            self.num_in_series.grid_forget()
            self.num_in_series_entry.grid_forget()

            self.success_label.grid(row=8, column=1)
            self.app.load_books()
        else:
            self.error_label.config(text=f"Error: {db_attempt}!", fg="red")
            self.error_label.grid(row=8, column=1)

    def refresh_authors(self):
        self.authors =  db_get.get_authors()
        amap = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }
        self.author_map = amap
        self.author_dropdown.configure(values=list(self.author_map.keys()))

    def refresh_genres(self):
        self.genres = db_get.get_genres_titles()
        genre = {
            f"{title}": genre_id
            for genre_id, title in self.genres
        }
        self.genre_map = genre
        self.genre_dropdown.configure(values=list(self.genre_map.keys()))