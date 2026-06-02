import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from db import database, db_get
from book_table import BookTable
from windows.x.add_data_window import AddDataWindow


# TODO: color coding based on genre
# TODO: backups manual
# TODO: description/review
# TODO: row seperators - not possible
# TODO: research print function
# TODO: research  built in mp3 player
# TODO: xbox 360 games

class MyBookManager:

    def __init__(self, root):
        super().__init__()
        self.root=root
        self.root.title("MyBook Manager")
        # self.root.geometry("1280x800")

        self.center_window(1280, 800)


        self.author_map = {}

        top_frame = tk.Frame(self.root, height=20)
        top_frame.pack(side="top", fill="x", anchor="n", pady=(0,5))

        center_frame = tk.Frame(self.root)
        center_frame.pack(side="top", fill="both", anchor="n")

        btn = ctk.CTkButton(top_frame, text=" + ", command=self.open_add_window, height=30, width=30, corner_radius=5, border_color="blue", font=("Arial", 30))
        btn.pack(side="left", padx=5, pady=5)

        self.add_window = None

        # App label name
        label1 = tk.Label(top_frame, text="MyBook Manager", font=("Arial", 14, "bold"), fg="lightblue")
        label1.pack(side="right", padx=5)

        self.load_mode = tk.StringVar()
        self.load_mode.set("Default")

        tk.Label(center_frame, text="Filter:").grid(row=0, column=0)

        mode_dropdown = ttk.Combobox(
            center_frame,
            textvariable=self.load_mode,
            values=["Default", "By Author"],
            state="readonly",
            width=15
        )

        mode_dropdown.grid(row=0, column=3)
        mode_dropdown.bind("<<ComboboxSelected>>", self.on_mode_change)

        self.author_filter_var = tk.StringVar()

        self.author_filter = ttk.Combobox(
            center_frame,
            textvariable=self.author_filter_var,
            state="readonly"
        )
        self.author_filter.grid(row=0, column=6)

        self.author_filter.grid_forget()  # hidden initially

        tk.Button(
            center_frame,
            text="Load Books",
            command=self.load_books
        ).grid(row=0, column=1000)

        # =========================
        # TABLE
        # =========================

        self.book_table = BookTable(root)
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

        else:
            books = db_get.get_books()

        self.book_table.populate_table(books)


    def on_mode_change(self, event=None):

        mode = self.load_mode.get()

        if mode == "By Author":
            self.load_authors_into_filter()
            self.author_filter.grid(row=0, column=6)
        else:
            self.author_filter.grid_forget()

    def load_authors_into_filter(self):

        authors = db_get.get_authors()

        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in authors
        }

        self.author_filter["values"] = list(self.author_map.keys())

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

root = ctk.CTk()

database.create_tables()

app = MyBookManager(root)

root.mainloop()