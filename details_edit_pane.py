import threading
import customtkinter as ctk
# import tkinter as tk
import PIL.Image as Image

from db import db_get, db_update, db_add
from windows.settings_helpers.cover_fetcher import auto_fetch_and_save_book_cover
from windows.book_tabs.helpers.topics_scrollable import TopicsFrame


class DetailsEditPane(ctk.CTkFrame):
    def __init__(self, parent, par, app, data):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.par = par
        self.app = app
        self.book = data

        self.authors = db_get.get_authors()
        self.topics = db_get.get_topics()
        series = db_get.get_series_by_author(self.book[5]) if self.book[5] is not None else []
        self.genres = db_get.get_genres_titles()
        self.topic_ids = db_get.get_book_topics_id(self.book[0])

        self.style = {
            "width": 250,
            "border_color": ("gray70", "gray40"),
            "border_width": 1,
        }

        self.pad = {
            "pady": 1,
            "padx": 5
        }

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(side="top", anchor="n", fill="x", expand=True)
        # bar.columnconfigure(1, weight=1)
        bar.columnconfigure(2, weight=1)

        details = ctk.CTkFrame(self, fg_color="transparent")
        details.pack(side="top", anchor="n", fill="x", expand=True)
        details.columnconfigure(0, weight=1, uniform="group1")
        details.columnconfigure(1, weight=1, uniform="group1")

        col1 = ctk.CTkFrame(details, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="nsew")
        col2 = ctk.CTkFrame(details, fg_color="transparent")
        col2.grid(row=0, column=1, sticky="nsew")
        col3 = ctk.CTkFrame(details, fg_color="transparent")
        col3.grid(row=0, column=2, sticky="nsew")

        close_pil = Image.open('assets/img/close_btn.png').convert('RGBA')
        close_img = ctk.CTkImage(light_image=close_pil, dark_image=close_pil, size=(16, 16))

        self.edit_btn = ctk.CTkButton(bar, text="SAVE", width=50, fg_color="#238636", hover_color="#2ea043", command=lambda: self.save_book())
        self.edit_btn.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.cancel_btn = ctk.CTkButton(bar, text="CANCEL", width=50, fg_color="#cf222e", hover_color="#f85149", command=lambda: self.par.load_book(self.book[0]))
        self.cancel_btn.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.error_msg = ctk.CTkLabel(bar, text="", text_color="red")

        close_btn = ctk.CTkButton(bar, image=close_img, text="", width=20, height=20, fg_color="transparent", hover_color=("gray80", "gray30"), command=self.app.close_book)
        close_btn.grid(row=0, column=2, sticky="e", padx=5, pady=2)

        # Title
        ctk.CTkLabel(col1, text="Title:").grid(row=0, column=0, sticky="e", **self.pad)
        self.title_entry = ctk.CTkEntry(col1, **self.style)
        self.title_entry.grid(row=0, column=1, sticky="w", **self.pad)
        if self.book[1] is not None:
            self.title_entry.insert(0, str(self.book[1]))

        # Author
        ctk.CTkLabel(col1, text="Author:").grid(row=1, column=0, sticky="e", **self.pad)
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

        dropdown = ctk.CTkComboBox(
            col1,
            variable=self.selected_author,
            values=list(self.author_map.keys()),
            command=self.author_selected,
            **self.style
        )
        if self.book[5] in self.author_id_map:
            self.selected_author.set(self.author_id_map[self.book[5]])
        elif self.book[6] or self.book[7]:
            author_display = f"{self.book[6] or ''} {self.book[7] or ''}".strip()
            self.selected_author.set(author_display)
            if self.book[5] is not None:
                self.author_map[author_display] = self.book[5]
        dropdown.grid(row=1, column=1, sticky="w", **self.pad)
        # self.selected_author.trace_add("write", self.author_selected)


        # Series
        self.series_id = self.book[2]
        self.selected_series = ctk.StringVar()
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
            if self.book[2] in self.series_id_map:
                self.selected_series.set(self.series_id_map[self.book[2]])
            elif self.book[3]:
                self.selected_series.set(str(self.book[3]))
                self.series_map[str(self.book[3])] = self.series_id

        self.series_dropdown = ctk.CTkComboBox(
            col1,
            values=list(self.series_map.keys()),
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
        if self.book[4] is not None:
            self.book_num_entry.insert(0, str(self.book[4]))

        # Genre
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
        if self.book[9] is not None:
            self.selected_genre.set(str(self.book[9]))
        self.genre_dropdown.grid(row=4, column=1, sticky="w", **self.pad)

        # ISBN
        ctk.CTkLabel(col1, text="ISBN:").grid(row=5, column=0, sticky="e", **self.pad)
        self.isbn_entry = ctk.CTkEntry(col1, **self.style)
        self.isbn_entry.grid(row=5, column=1, sticky="w", **self.pad)
        if self.book[10] is not None:
            self.isbn_entry.insert(0, str(self.book[10]))

        # Rating
        ctk.CTkLabel(col2, text="Rating:").grid(row=0, column=0, sticky="e", **self.pad)
        self.rating_entry = ctk.CTkEntry(col2, **self.style)
        self.rating_entry.grid(row=0, column=1, sticky="w", **self.pad)
        if self.book[8] is not None:
            self.rating_entry.insert(0, str(self.book[8]))

        # NLS Order
        ctk.CTkLabel(col2, text="NLS Order:").grid(row=1, column=0, sticky="e", **self.pad)
        self.nls_order_entry = ctk.CTkEntry(col2, **self.style)
        self.nls_order_entry.grid(row=1, column=1, sticky="w", **self.pad)
        if self.book[11] is not None:
            self.nls_order_entry.insert(0, str(self.book[11]))

        # Description
        ctk.CTkLabel(col2, text="Description:").grid(row=2, column=0, sticky="ne", **self.pad)
        self.description_entry = ctk.CTkTextbox(col2, **self.style, height=100)
        self.description_entry.grid(row=2, column=1, sticky="w", **self.pad)
        if self.book[12] is not None:
            self.description_entry.insert("0.0", str(self.book[12]))

        #Topics frame
        ctk.CTkLabel(col3, text="Topics:").grid(row=0, column=0, sticky="ne", **self.pad)
        self.topics_frame = TopicsFrame(col3, self.topics)
        self.topics_frame.grid(row=0, column=1, sticky="w", pady=2)
        self.topics_frame.set_selected_topics(self.topic_ids)
        self.topics_frame.configure(width=140)


    def author_selected(self, name):
        author_id = self.author_map.get(name)
        if author_id is None:
            return

        # Get series from database
        series = db_get.get_series_by_author(author_id)

        smap = {
            f"{title}": series_id
            for series_id, title in series
        }
        self.series_map = smap
        self.series_dropdown.configure(values=list(self.series_map.keys()))

        if not self.series_map:
            self.selected_series.set("")
            self.series_id = None
        else:
            # Show dropdown only AFTER author selected
            self.series_label.grid(row=2, column=0, sticky="e", **self.pad)
            self.series_dropdown.grid(row=2, column=1, sticky="w", **self.pad)
            if series:
                self.selected_series.set(series[0][1])

    def save_book(self):
        book_id = self.book[0]
        title = self.title_entry.get().strip()
        author_name = self.selected_author.get().strip()
        series = self.selected_series.get().strip()

        if not series:
            series_id = None
        else:
            series_id = self.series_map.get(series)

        book_num = self.book_num_entry.get().strip()
        rating = self.rating_entry.get().strip()
        genre = self.selected_genre.get().strip()

        if not genre:
            genre_id = None
        else:
            genre_id = self.genre_map.get(genre)

        isbn = self.isbn_entry.get().strip()
        nls = self.nls_order_entry.get().strip()
        desc = self.description_entry.get("1.0", "end-1c").strip()
        topics = self.topics_frame.get_selected_topics()

        author_id = self.author_map.get(author_name)

        data = (title, author_id, series_id, book_num, rating, genre_id, isbn, nls, desc, book_id)
        db_attempt = db_update.update_book(data)
        if db_attempt == "success":
            topics_remove = db_update.remove_book_topic((book_id,))
            if topics_remove == "success":
                success = True
                if topics:
                    for topics_id in topics:
                        topics_data = (book_id, topics_id)
                        topics_db_attempt = db_add.add_book_topics(topics_data)
                        if not isinstance(topics_db_attempt, tuple) or topics_db_attempt[0] != "success":
                            success = False
                            print(topics_db_attempt)
                            self.error_msg.configure(text=f"Error: {topics_db_attempt}")
                            self.error_msg.grid(row=0, column=2, sticky="w", padx=5, pady=2)
                            break
                if success:
                    if isbn:
                        def _bg_check_cover(bid, book_isbn, details_frame):
                            try:
                                existing_cover = db_get.get_book_cover(bid)
                                if not existing_cover:
                                    fetched, _ = auto_fetch_and_save_book_cover(bid, book_isbn)
                                    if fetched and hasattr(details_frame, "load_cover_image"):
                                        details_frame.after(0, lambda: details_frame.load_cover_image(bid))
                            except Exception as e:
                                print("Error checking cover on edit save:", e)
                        threading.Thread(target=_bg_check_cover, args=(self.book[0], isbn, self.par), daemon=True).start()

                    self.par.load_book(self.book[0])
                    self.app.load_books()
            else:
                print(topics_remove)
                self.error_msg.configure(text=f"Error: {topics_remove}")
                self.error_msg.grid(row=0, column=2, sticky="w", padx=5, pady=2)
        else:
            self.error_msg.configure(text=f"Error: {db_attempt}")
            self.error_msg.grid(row=0, column=2, sticky="w", padx=5, pady=2)