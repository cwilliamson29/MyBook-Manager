import customtkinter as ctk
# import tkinter as tk
import requests
import PIL.Image as Image
from io import BytesIO

from PIL import ImageTk

from db import db_get, db_update


class DetailsEditPane(ctk.CTkFrame):
    def __init__(self, parent, par, app, data):
        super().__init__(parent)
        self.parent = parent
        self.par = par
        self.app = app
        self.book = data

        self.style = {
            "width": 250,
            "border_color": "gray40",
            "border_width": 1,
        }

        self.pad = {
            "pady": 1,
            "padx": 5
        }

        bar = ctk.CTkFrame(self, border_color="blue", border_width=1)
        bar.pack(side="top", anchor="n", fill="x", expand=True)
        bar.columnconfigure(1, weight=1)

        details = ctk.CTkFrame(self, border_color="red", border_width=1)
        details.pack(side="top", anchor="n", fill="x", expand=True)
        details.columnconfigure(0, weight=1, uniform="group1")
        details.columnconfigure(1, weight=1, uniform="group1")

        col1 = ctk.CTkFrame(details, border_color="blue", border_width=1)
        col1.grid(row=0, column=0, sticky="nsew")
        col2 = ctk.CTkFrame(details, border_color="blue", border_width=1)
        col2.grid(row=0, column=1, sticky="nsew")

        close_img = Image.open('assets/img/close_btn.png').convert('RGBA')
        close_img = close_img.resize((20, 20))
        close_img_display = ImageTk.PhotoImage(close_img)

        self.edit_btn = ctk.CTkButton(bar, text="SAVE", width=50, fg_color="green", hover_color="darkgreen", command=lambda: self.save_book())
        self.edit_btn.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.cancel_btn = ctk.CTkButton(bar, text="CANCEL", width=50, fg_color="red", hover_color="darkred", command=lambda: self.par.load_book(self.book[0]))
        self.cancel_btn.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        close_btn = ctk.CTkButton(bar, image=close_img_display, text=None, width=20, fg_color="transparent", command=self.app.close_book)
        close_btn.image = close_img_display
        close_btn.grid(row=0, column=2, sticky="e", padx=5, pady=2)

        # Title
        ctk.CTkLabel(col1, text="Title:").grid(row=0, column=0, sticky="e", **self.pad)
        self.title_entry = ctk.CTkEntry(col1, **self.style)
        self.title_entry.grid(row=0, column=1, sticky="w", **self.pad)
        self.title_entry.insert(0, self.book[1])

        # Author
        ctk.CTkLabel(col1, text="Author:").grid(row=1, column=0, sticky="e", **self.pad)
        self.authors = db_get.get_authors()
        self.selected_author = ctk.StringVar()
        # map display name -> id
        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }
        self.author_id_map = {
            author_id: f"{first} {last}"
            for author_id, first, last in self.authors
        }
        # self.dropdown = ctk.CTkOptionMenu(
        #     self,
        #     self.selected_author,
        #     *self.author_map.keys()
        # )
        dropdown = ctk.CTkComboBox(
            col1,
            variable=self.selected_author,
            values=list(self.author_map.keys()),
            **self.style
        )
        self.selected_author.set(
            self.author_id_map[self.book[5]]
        )
        dropdown.grid(row=1, column=1, sticky="w", **self.pad)
        self.selected_author.trace_add("write", self.author_selected)


        # Series
        self.series_id = self.book[2]
        self.selected_series = ctk.StringVar()
        series = db_get.get_series_by_author(self.book[5])
        self.series_label = ctk.CTkLabel(col1, text="Series:")
        self.series_map = {
            f"{title}": series_id
            for series_id, title in series
        }
        self.series_id_map = {
            series_id: f"{title}"
            for series_id, title in series
        }
        if self.series_id is not None:
            self.selected_series.set(self.series_id_map[self.book[2]])

        self.series_dropdown = ctk.CTkComboBox(
            col1,
            values=list(self.series_map),
            variable=self.selected_series,
            **self.style
        )
        # series_entry.insert(0, self.book[2])
        self.series_label.grid(row=2, column=0, sticky="e", **self.pad)
        self.series_dropdown.grid(row=2, column=1, sticky="w", **self.pad)

        # Book number
        ctk.CTkLabel(col1, text="Book #:").grid(row=3, column=0, sticky="e", **self.pad)
        self.book_num_entry = ctk.CTkEntry(col1, **self.style)
        self.book_num_entry.grid(row=3, column=1, sticky="w", **self.pad)
        self.book_num_entry.insert(0, self.book[4])

        # Genre
        self.genres = db_get.get_genres_titles()

        ctk.CTkLabel(col1, text="Genre:").grid(row=4, column=0, sticky="e", **self.pad)
        self.selected_genre = ctk.StringVar()
        self.genre_map = {
            f"{title}": genre_id
            for genre_id, title in self.genres
        }
        self.genre_dropdown = ctk.CTkComboBox(
            col1,
            values=list(self.genre_map.keys()),
            variable=self.selected_genre,
            **self.style
        )
        self.selected_genre.set(self.book[9])
        self.genre_dropdown.grid(row=4, column=1, sticky="w", **self.pad)

        # ISBN
        ctk.CTkLabel(col1, text="ISBN:").grid(row=5, column=0, sticky="e", **self.pad)
        self.isbn_entry = ctk.CTkEntry(col1, **self.style)
        self.isbn_entry.grid(row=5, column=1, sticky="w", **self.pad)
        self.isbn_entry.insert(0, self.book[10])

        # Rating
        ctk.CTkLabel(col2, text="Rating:").grid(row=0, column=0, sticky="e", **self.pad)
        self.rating_entry = ctk.CTkEntry(col2, **self.style)
        self.rating_entry.grid(row=0, column=1, sticky="w", **self.pad)
        self.rating_entry.insert(0, self.book[8])

        # NLS Order
        ctk.CTkLabel(col2, text="NLS Order:").grid(row=1, column=0, sticky="e", **self.pad)
        self.nls_order_entry = ctk.CTkEntry(col2, **self.style)
        self.nls_order_entry.grid(row=1, column=1, sticky="w", **self.pad)
        self.nls_order_entry.insert(0, self.book[11])

        # Description
        ctk.CTkLabel(col2, text="Description:").grid(row=2, column=0, sticky="ne", **self.pad)
        self.description_entry = ctk.CTkTextbox(col2, **self.style, height=100)
        self.description_entry.grid(row=2, column=1, sticky="w", **self.pad)
        if self.book[12] is not None:
            self.description_entry.insert("0.0", self.book[12])

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
            # self.num_in_series.grid_forget()
            # self.num_in_series_entry.grid_forget()
        else:
            # Show dropdown only AFTER author selected
            self.series_label.grid(row=2, column=0, sticky="e", **self.pad)
            self.series_dropdown.grid(row=2, column=1, sticky="w", **self.pad)
            # self.num_in_series.grid(row=3, column=0, sticky="e", pady=2)
            # self.num_in_series_entry.grid(row=3, column=1, sticky="w", pady=2)

        # Set default value
        if series:
            self.selected_series.set(series[0][1])

    def save_book(self, *args):
        book_id = self.book[0]
        title = self.title_entry.get().strip()
        author_name = self.selected_author.get()
        series = self.selected_series.get()

        if not series:
            series_id = None
        else:
            series_id = self.series_map[series]

        book_num = self.book_num_entry.get().strip()
        rating = self.rating_entry.get().strip()
        genre = self.selected_genre.get()

        if not genre:
            genre_id = None
        else:
            genre_id = self.genre_map[genre]

        isbn = self.isbn_entry.get().strip()
        nls = self.nls_order_entry.get().strip()
        desc = self.description_entry.get("1.0", "end-1c").strip()

        author_id = self.author_map[author_name]

        data = (title, author_id, series_id, book_num, rating, genre_id, isbn, nls, desc, book_id)
        db_attempt = db_update.update_book(data)
        if db_attempt == "success":
            print("success")
        else:
            print('failed')