import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk


from db import database, db_get
from book_table import BookTable
from details_frame import DetailsFrame
from windows.add_data_window import AddDataWindow


# TODO: backups manual
# TODO: Settings Window
# TODO: mp3 playback
# TODO: Menu bar
# TODO: research print function
# TODO: research  built in mp3 player
# TODO: Topics/categries

class MyBookManager:

    def __init__(self, root):
        super().__init__()
        self.root=root
        self.root.title("MyBook Manager")

        self.center_window(1280, 800)

        img_path = "assets/img/gear-icon.webp"
        img = Image.open(img_path)
        img = img.resize((33,33),)
        gear_img = ImageTk.PhotoImage(img)

        self.author_map = {}
        self.topic_map = {}

        self.add_window = None


        # App frames
        top_frame = tk.Frame(self.root, height=20)
        top_frame.pack(side="top", fill="x", anchor="n")
        top_frame.columnconfigure(2, weight=1)

        # outer_details = tk.Frame(self.root, background="gray20")
        # outer_details.pack(side="top", fill="x", anchor="n")
        self.details_framed = tk.Frame(self.root, background="gray20")
        self.details_framed.pack(side="top", fill="x", anchor="n")

        self.center_frame = tk.Frame(self.root)
        self.center_frame.pack(side="top", fill="both", anchor="n")

        #############################
        # Top frame buttons and label
        #############################
        add_btn = ctk.CTkButton(top_frame, text=" + ", command=self.open_add_window, height=30, width=30, corner_radius=5, border_color="blue", font=("Arial", 30))
        add_btn.grid(row=0, column=0, padx=4, pady=5)

        settings_btn = ctk.CTkButton(top_frame, image=gear_img, text="", command=self.open_add_window, height=30, width=30, corner_radius=5, border_color="blue", font=("Arial", 30))
        settings_btn.grid(row=0, column=1, padx=4, pady=5)

        app_label = tk.Label(top_frame, text="MyBook Manager", font=("Arial", 14, "bold"), fg="lightblue")
        app_label.grid(row=0, column=2, sticky="e", padx=4, pady=5)

        # self.book_id = tk.StringVar()
        self.details = DetailsFrame(self.details_framed, self)
        self.details.pack_forget()

        #########################
        # Center frame components
        #########################
        self.load_mode = tk.StringVar()
        self.load_mode.set("Default")

        tk.Label(self.center_frame, text="Filter:").grid(row=0, column=0)

        mode_dropdown = ttk.Combobox(
            self.center_frame,
            textvariable=self.load_mode,
            values=["Default", "By Author", "By Topic"],
            state="readonly",
            width=15
        )

        mode_dropdown.grid(row=0, column=3)
        mode_dropdown.bind('<<ComboboxSelected>>', self.on_mode_change)

        self.author_filter_var = tk.StringVar()

        self.author_filter = ttk.Combobox(
            self.center_frame,
            textvariable=self.author_filter_var,
            state="readonly"
        )
        self.author_filter.grid(row=0, column=6)

        self.author_filter.grid_forget()  # hidden initially

        self.topic_filter_var = tk.StringVar()

        self.topic_filter = ttk.Combobox(
            self.center_frame,
            textvariable=self.topic_filter_var,
            state="readonly"
        )
        self.topic_filter.grid(row=0, column=7)

        self.topic_filter.grid_forget()

        tk.Button(
            self.center_frame,
            text="Load Books",
            command=self.load_books
        ).grid(row=0, column=1000)

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
        else:
            books = db_get.get_books()

        self.book_table.populate_table(books)


    def on_mode_change(self, event=None):

        mode = self.load_mode.get()

        if mode == "By Author":
            self.topic_filter.grid_forget()

            self.load_authors_into_filter()
            self.author_filter.grid(row=0, column=6)
        elif mode == "By Topic":
            self.author_filter.grid_forget()

            self.load_topics_into_filter()
            self.topic_filter.grid(row=0, column=7)
        else:
            self.author_filter.grid_forget()
            self.topic_filter.grid_forget()

    def load_authors_into_filter(self):

        authors = db_get.get_authors()

        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in authors
        }

        self.author_filter["values"] = list(self.author_map.keys())

    def load_topics_into_filter(self):
        topics = db_get.get_topics()

        self.topic_map = {
            f"{name}": topic_id
            for topic_id, name in topics
        }
        self.topic_filter["values"] = list(self.topic_map.keys())

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

    def show_book_details(self, book_id):
        self.details_framed.pack(side="top", fill="x", anchor="n", before=self.center_frame)
        self.details.pack(side="top", fill="x", anchor="n")
        # book = get_book_details(book_id)
        self.details.load_book(book_id)

    def close_book(self):
        self.details_framed.pack_forget()
        self.details.pack_forget()


ctk.set_appearance_mode("Dark")

root = ctk.CTk()
root.fg_color="gray20"

database.create_tables()

app = MyBookManager(root)

root.mainloop()