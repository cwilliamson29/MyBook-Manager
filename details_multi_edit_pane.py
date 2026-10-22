import customtkinter as ctk
import PIL.Image as Image

from db import db_get, db_update
from windows.book_tabs.helpers.topics_scrollable import TopicsFrame


class DetailsMultiEditPane(ctk.CTkFrame):
    def __init__(self, parent, par, app, book_ids):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.par = par
        self.app = app
        self.book_ids = list(book_ids)

        self.genres = db_get.get_genres_titles()
        self.topics = db_get.get_topics()

        # Genre map: title -> id
        self.genre_map = {
            f"{title}": genre_id
            for genre_id, title in self.genres
        }

        self.style = {
            "width": 250,
            "border_color": ("gray70", "gray40"),
            "border_width": 1,
        }

        self.pad = {
            "pady": 2,
            "padx": 5
        }

        # Top action bar
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(side="top", anchor="n", fill="x", expand=True)
        bar.columnconfigure(3, weight=1)

        close_pil = Image.open('assets/img/close_btn.png').convert('RGBA')
        close_img = ctk.CTkImage(light_image=close_pil, dark_image=close_pil, size=(16, 16))

        self.save_btn = ctk.CTkButton(
            bar,
            text=f"APPLY TO SELECTED ({len(self.book_ids)})",
            fg_color="#238636",
            hover_color="#2ea043",
            command=self.save_bulk
        )
        self.save_btn.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.cancel_btn = ctk.CTkButton(
            bar,
            text="CANCEL",
            width=60,
            fg_color="#cf222e",
            hover_color="#f85149",
            command=self.app.close_book
        )
        self.cancel_btn.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.error_msg = ctk.CTkLabel(bar, text="", text_color="red", font=("Arial", 12, "bold"))
        self.error_msg.grid(row=0, column=2, sticky="w", padx=10, pady=2)

        close_btn = ctk.CTkButton(
            bar,
            image=close_img,
            text="",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=self.app.close_book
        )
        close_btn.grid(row=0, column=3, sticky="e", padx=5, pady=2)

        # Main details frame
        details = ctk.CTkFrame(self, fg_color="transparent")
        details.pack(side="top", anchor="n", fill="x", expand=True, pady=4)
        details.columnconfigure(0, weight=1, uniform="group1")
        details.columnconfigure(1, weight=1, uniform="group1")
        details.columnconfigure(2, weight=1, uniform="group1")

        col1 = ctk.CTkFrame(details, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="nsew", padx=5, pady=2)
        col2 = ctk.CTkFrame(details, fg_color="transparent")
        col2.grid(row=0, column=1, sticky="nsew", padx=5, pady=2)
        col3 = ctk.CTkFrame(details, fg_color="transparent")
        col3.grid(row=0, column=2, sticky="nsew", padx=5, pady=2)

        # ------------------------------------
        # Column 1: Genre Selection
        # ------------------------------------
        self.update_genre_var = ctk.BooleanVar(value=True)
        self.genre_check = ctk.CTkCheckBox(
            col1,
            text="Update Genre",
            variable=self.update_genre_var,
            font=("Arial", 13, "bold"),
            command=self.toggle_genre_state
        )
        self.genre_check.grid(row=0, column=0, columnspan=2, sticky="w", **self.pad)

        ctk.CTkLabel(col1, text="Genre:").grid(row=1, column=0, sticky="e", **self.pad)
        self.selected_genre = ctk.StringVar()
        genre_values = list(self.genre_map.keys())
        if genre_values:
            self.selected_genre.set(genre_values[0])

        self.genre_dropdown = ctk.CTkComboBox(
            col1,
            values=genre_values,
            variable=self.selected_genre,
            **self.style
        )
        self.genre_dropdown.grid(row=1, column=1, sticky="w", **self.pad)

        # ------------------------------------
        # Column 2: Topics Selection
        # ------------------------------------
        self.update_topics_var = ctk.BooleanVar(value=True)
        self.topics_check = ctk.CTkCheckBox(
            col2,
            text="Update Topics",
            variable=self.update_topics_var,
            font=("Arial", 13, "bold"),
            command=self.toggle_topics_state
        )
        self.topics_check.grid(row=0, column=0, columnspan=2, sticky="w", **self.pad)

        topic_btn_frame = ctk.CTkFrame(col2, fg_color="transparent")
        topic_btn_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        select_all_btn = ctk.CTkButton(
            topic_btn_frame,
            text="Select All",
            width=70,
            height=22,
            font=("Arial", 11),
            fg_color=("#e1e4e8", "#30363d"),
            hover_color=("#d0d7de", "#484f58"),
            text_color=("#1f2328", "#f0f6fc"),
            command=self.select_all_topics
        )
        select_all_btn.pack(side="left", padx=2)

        clear_all_btn = ctk.CTkButton(
            topic_btn_frame,
            text="Clear All",
            width=70,
            height=22,
            font=("Arial", 11),
            fg_color=("#e1e4e8", "#30363d"),
            hover_color=("#d0d7de", "#484f58"),
            text_color=("#1f2328", "#f0f6fc"),
            command=self.clear_all_topics
        )
        clear_all_btn.pack(side="left", padx=2)

        self.topics_frame = TopicsFrame(col2, self.topics)
        self.topics_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=2)

        # ------------------------------------
        # Column 3: Selected Books Overview
        # ------------------------------------
        ctk.CTkLabel(
            col3,
            text=f"Selected Books ({len(self.book_ids)}):",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=5, pady=2)

        self.preview_box = ctk.CTkTextbox(
            col3,
            height=120,
            width=260,
            fg_color=("#ffffff", "#2b2b2b"),
            text_color=("#1f2328", "white"),
            font=("Arial", 11)
        )
        self.preview_box.pack(fill="both", expand=True, padx=5, pady=2)
        self.populate_preview()

    def populate_preview(self):
        titles = []
        for b_id in self.book_ids:
            row = db_get.get_book_by_id(b_id)
            if row:
                title = row[0][1] if row[0][1] is not None else f"Book #{b_id}"
                author = f"{row[0][6] or ''} {row[0][7] or ''}".strip()
                if author:
                    titles.append(f"• {title} ({author})")
                else:
                    titles.append(f"• {title}")
        self.preview_box.insert("0.0", "\n".join(titles))
        self.preview_box.configure(state="disabled")

    def toggle_genre_state(self):
        if self.update_genre_var.get():
            self.genre_dropdown.configure(state="normal")
        else:
            self.genre_dropdown.configure(state="disabled")

    def toggle_topics_state(self):
        pass

    def select_all_topics(self):
        if not self.update_topics_var.get():
            self.update_topics_var.set(True)
        for var in self.topics_frame.topics_vars.values():
            var.set(True)

    def clear_all_topics(self):
        self.topics_frame.clear()

    def save_bulk(self):
        update_genre = self.update_genre_var.get()
        update_topics = self.update_topics_var.get()

        if not update_genre and not update_topics:
            self.error_msg.configure(text="Please select at least one field to update (Genre or Topics).")
            return

        genre_id = None
        if update_genre:
            genre_name = self.selected_genre.get().strip()
            if not genre_name:
                self.error_msg.configure(text="Please choose a genre.")
                return
            genre_id = self.genre_map.get(genre_name)

        topic_ids = None
        if update_topics:
            topic_ids = self.topics_frame.get_selected_topics()

        res = db_update.bulk_update_genre_and_topics(
            book_ids=self.book_ids,
            genre_id=genre_id,
            update_genre=update_genre,
            topic_ids=topic_ids,
            update_topics=update_topics
        )

        if res == "success":
            self.app.load_books()
            self.app.close_book()
        else:
            self.error_msg.configure(text=f"Error: {res}")
