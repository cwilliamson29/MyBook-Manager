import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from windows.addSeries_Window import AddSeriesWindow
from windows.add_author_window import AddAuthorWindow
from db import database, db_get
from windows.add_book_window import AddBookWindow
from book_table import BookTable
from windows.add_data_window import AddDataWindow


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
        self.root.geometry("1280x800")

        top_frame = tk.Frame(self.root, height=20)
        top_frame.pack(side="top", fill="x", anchor="n", pady=(0,5))

        center_frame = tk.Frame(self.root)
        center_frame.pack(side="top", fill="both", anchor="n")

        # # Top frame buttons
        # open_author_btn = tk.Button(top_frame, text="Add Author", command=self.open_add_author)
        # open_author_btn.pack(side="left", padx=5)
        # self.add_author_window = None
        #
        # open_series_btn = tk.Button(top_frame, text="Add Series", command=self.add_series_window)
        # open_series_btn.pack(side="left", padx=5)
        # self.addSeries_Window = None
        #
        # open_book_btn = tk.Button(top_frame, text="Add Book", command=self.open_add_book)
        # open_book_btn.pack(side="left", padx=5)
        # self.add_book_window = None
        btn = ctk.CTkButton(top_frame, text="Add ctk", command=self.open_add_window, height=25, width=25, corner_radius=50)
        btn.pack(side="left")
        open_add_window = tk.Button(top_frame, text="Add", command=self.open_add_window, height=2, width=2)
        open_add_window.pack(side="left", padx=5)
        self.add_book_window = None

        # App label name
        label1 = tk.Label(top_frame, text="MyBook Manager", font=("Arial", 14, "bold"), fg="blue")
        label1.pack(side="right", padx=5)

        self.load_mode = tk.StringVar()
        self.load_mode.set("Default")

        tk.Label(center_frame, text="Load Mode:").grid(row=0, column=0)

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

        # self.load_authors_into_filter()
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

    # ----------
    # Windows
    #-----------
    def open_add_window(self):

        AddDataWindow(self)

    def add_series_window(self):
        # If window already exists, bring it to front
        if self.addSeries_Window is not None and self.addSeries_Window.winfo_exists():
            self.addSeries_Window.lift()
            self.addSeries_Window.focus_force()
            return

        # Create new window
        self.addSeries_Window = AddSeriesWindow(self)

    def open_add_author(self):

        if self.add_author_window is not None and self.add_author_window.winfo_exists():
            self.add_author_window.lift()
            self.add_author_window.focus_force()
            return


        self.add_author_window = AddAuthorWindow(self)

    def open_add_book(self):

        if self.add_book_window is not None and self.add_book_window.winfo_exists():
            self.add_book_window.lift()
            return

        self.add_book_window = AddBookWindow(self)

root = ctk.CTk()
database.create_tables()
app = MyBookManager(root)

root.mainloop()