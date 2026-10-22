import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image


from db import database, db_get
from book_table import BookTable
from details_frame import DetailsFrame
from windows.add_data_window import AddDataWindow
from windows.settings_window import SettingsWindow


# TODO: backups manual
# TODO: Settings Window
# TODO: mp3 playback
# TODO: Menu bar
# TODO: research print function
# TODO: research  built in mp3 player

class MyBookManager:

    def __init__(self, root):
        super().__init__()
        self.root=root
        self.root.title("MyBook Manager")

        self.center_window(1280, 800)

        img_path = "assets/img/gear-icon.webp"
        gear_pil = Image.open(img_path)
        gear_img = ctk.CTkImage(light_image=gear_pil, dark_image=gear_pil, size=(22, 22))

        self.author_map = {}
        self.topic_map = {}
        self.genre_map = {}

        self.add_window = None
        self.settings_window = None


        # App frames
        top_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        top_frame.pack(side="top", fill="x", anchor="n", padx=10, pady=(6, 2))
        top_frame.columnconfigure(2, weight=1)

        self.details_framed = ctk.CTkFrame(self.root, fg_color="transparent")

        self.center_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.center_frame.pack(side="top", fill="x", anchor="n", padx=10, pady=4)

        #############################
        # Top frame buttons and label
        #############################
        add_btn = ctk.CTkButton(top_frame, text="+", command=self.open_add_window, height=36, width=36, corner_radius=5, font=("Arial", 20, "bold"))
        add_btn.grid(row=0, column=0, padx=4, pady=5)

        settings_btn = ctk.CTkButton(top_frame, image=gear_img, text="", command=self.open_settings_window, height=36, width=36, corner_radius=5)
        settings_btn.grid(row=0, column=1, padx=4, pady=5)

        app_label = ctk.CTkLabel(top_frame, text="MyBook Manager", font=("Arial", 16, "bold"), text_color=("#0969da", "#58a6ff"))
        app_label.grid(row=0, column=2, sticky="e", padx=4, pady=5)

        # self.book_id = tk.StringVar()
        self.details = DetailsFrame(self.details_framed, self)
        self.details.pack_forget()

        #########################
        # Center frame components
        #########################
        self.load_mode = tk.StringVar()
        self.load_mode.set("Default")

        ctk.CTkLabel(self.center_frame, text="Filter:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=(0, 6), pady=4)

        mode_dropdown = ctk.CTkComboBox(
            self.center_frame,
            variable=self.load_mode,
            values=["Default", "By Author", "By Genre", "By Topic", "By Genre & Topic"],
            command=self.on_mode_change,
            width=160
        )

        mode_dropdown.grid(row=0, column=3, padx=(0, 6), pady=4)

        # Author Filter
        self.author_filter_var = tk.StringVar()
        self.author_filter = ctk.CTkComboBox(
            self.center_frame,
            variable=self.author_filter_var,
            width=180
        )
        self.author_filter.grid(row=0, column=6, padx=(0, 6), pady=4)
        self.author_filter.grid_forget()  # hidden initially

        # Genre Filter
        self.genre_filter_var = tk.StringVar()
        self.genre_filter = ctk.CTkComboBox(
            self.center_frame,
            variable=self.genre_filter_var,
            width=180
        )
        self.genre_filter.grid(row=0, column=7, padx=(0, 6), pady=4)
        self.genre_filter.grid_forget()

        # Topic Filter
        self.topic_filter_var = tk.StringVar()
        self.topic_filter = ctk.CTkComboBox(
            self.center_frame,
            variable=self.topic_filter_var,
            width=180
        )
        self.topic_filter.grid(row=0, column=8, padx=(0, 6), pady=4)
        self.topic_filter.grid_forget()

        ctk.CTkButton(
            self.center_frame,
            text="Edit Selected",
            command=self.open_selected_edit,
            height=28,
            fg_color="#1f6feb",
            hover_color="#388bfd"
        ).grid(row=0, column=999, padx=5, pady=4)

        ctk.CTkButton(
            self.center_frame,
            text="Load Books",
            command=self.load_books,
            height=28,
            fg_color="#238636",
            hover_color="#2ea043"
        ).grid(row=0, column=1000, padx=5, pady=4)

        # =========================
        # TABLE
        # =========================

        self.book_table = BookTable(self.root, self)
        self.book_table.pack(fill="both", expand=True)

        self.load_books()

    def load_books(self):

        mode = self.load_mode.get()

        if mode == "Default":
            books = db_get.get_books()

        elif mode == "By Author":

            author_name = self.author_filter_var.get()

            if not author_name:
                return

            author_id = self.author_map[author_name]

            books = db_get.get_books_by_author(author_id)
        elif mode == "By Topic":
            topic_name = self.topic_filter_var.get()

            if not topic_name:
                return
            topic_id = self.topic_map[topic_name]
            books = db_get.get_books_by_topic(topic_id)
        elif mode == "By Genre":
            genre_name = self.genre_filter_var.get()
            if not genre_name:
                return
            genre_id = self.genre_map[genre_name]
            books = db_get.get_books_by_genre(genre_id)
        elif mode == "By Genre & Topic":
            genre_name = self.genre_filter_var.get()
            topic_name = self.topic_filter_var.get()
            if not topic_name:
                return
            if not genre_name:
                return
            genre_id = self.genre_map[genre_name]
            topic_id = self.topic_map[topic_name]
            books = db_get.get_books_by_topic_and_genre(topic_id, genre_id)
        else:
            books = db_get.get_books()

        self.book_table.populate_table(books)


    def on_mode_change(self, event=None):

        mode = self.load_mode.get()

        if mode == "By Author":
            self.topic_filter.grid_forget()
            self.genre_filter.grid_forget()

            self.load_authors_into_filter()
            self.author_filter.grid(row=0, column=6)
        elif mode == "By Topic":
            self.author_filter.grid_forget()
            self.genre_filter.grid_forget()

            self.load_topics_into_filter()
            self.topic_filter.grid(row=0, column=7)
        elif mode == "By Genre":
            self.author_filter.grid_forget()
            self.topic_filter.grid_forget()

            self.load_genres_into_filter()
            self.genre_filter.grid(row=0, column=8)
        elif mode == "By Genre & Topic":
            self.load_genres_into_filter()
            self.load_topics_into_filter()
            self.topic_filter.grid(row=0, column=8)
            self.genre_filter.grid(row=0, column=7)
        else:
            self.author_filter.grid_forget()
            self.topic_filter.grid_forget()
            self.genre_filter.grid_forget()

    def load_authors_into_filter(self):

        authors = db_get.get_authors()

        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in authors
        }
        print(self.author_map)
        self.author_filter.configure(values=list(self.author_map.keys()))

    def load_genres_into_filter(self):
        genres = db_get.get_genres_titles()
        # print(genres)
        self.genre_map = {
            f"{title}":genre_id
            for genre_id, title in genres
        }
        self.genre_filter.configure(values=list(self.genre_map.keys()))
        print(self.genre_map)

    def load_topics_into_filter(self):
        topics = db_get.get_topics()

        self.topic_map = {
            f"{name}": topic_id
            for topic_id, name in topics
        }
        self.topic_filter.configure(values=list(self.topic_map.keys()))

    def on_appearance_mode_changed(self, mode=None):
        if hasattr(self, "book_table"):
            self.book_table.update_theme()

    def center_window(self, width, height):

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )
    # ----------
    # Windows
    #-----------
    def open_add_window(self):
        if self.add_window is not None and self.add_window.winfo_exists():
            self.add_window.lift()
            self.add_window.focus_force()
            return

        self.add_window = AddDataWindow(self)

    def open_settings_window(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = SettingsWindow(self)

    def show_book_details(self, book_id):
        self.details_framed.pack(side="top", fill="x", anchor="n", before=self.center_frame)
        self.details.pack(side="top", fill="x", anchor="n")
        # book = get_book_details(book_id)
        self.details.load_book(book_id)

    def show_multi_book_details(self, book_ids):
        self.details_framed.pack(side="top", fill="x", anchor="n", before=self.center_frame)
        self.details.pack(side="top", fill="x", anchor="n")
        self.details.load_multi_books(book_ids)

    def open_selected_edit(self):
        selected = self.book_table.tree.selection()
        if not selected:
            return
        if len(selected) == 1:
            book_id = int(selected[0])
            self.show_book_details(book_id)
            self.details.edit_book(book_id)
        else:
            book_ids = [int(i) for i in selected]
            self.show_multi_book_details(book_ids)

    def close_book(self):
        self.details_framed.pack_forget()
        self.details.pack_forget()


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")

    root = ctk.CTk()

    database.create_tables()

    app = MyBookManager(root)

    root.mainloop()