import tkinter as tk
from tkinter import messagebox

from db import db_add, db_get


class AddBookWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent.root)

        self.parent = parent
        self.title("Add Book")
        self.geometry("350x275")

        row_frame = tk.Frame(self)
        row_frame.pack(padx=5, pady=1, side="top", anchor="w")

        row_frame2 = tk.Frame(self)
        row_frame2.pack(padx=5, pady=1, side="top", anchor="w")

        row_frame3 = tk.Frame(self)
        row_frame3.pack(padx=5, pady=1, side="top", anchor="w")

        row_frame4 = tk.Frame(self)
        row_frame4.pack(padx=5, pady=1, side="top", anchor="w")

        row_frame5 = tk.Frame(self)
        row_frame5.pack(padx=5, pady=1, side="top", anchor="w")

        row_frame6 = tk.Frame(self)
        row_frame6.pack(padx=5, pady=1, side="top", anchor="w")

        # Book title
        tk.Label(row_frame, text="Book Title:").pack(side="left", pady=5)

        self.title_entry = tk.Entry(row_frame, width=20)
        self.title_entry.pack(side="left")

        # Load authors
        self.authors = db_get.get_authors()

        tk.Label(row_frame2, text="Select Author:").pack(side="left", pady=5)

        self.selected_author = tk.StringVar()

        # map display name -> id
        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }
        self.dropdown = tk.OptionMenu(
            row_frame2,
            self.selected_author,
            *self.author_map.keys()
        )
        self.dropdown.pack(side="left")
        self.author_var = tk.StringVar()
        self.selected_author.trace_add("write", self.author_selected)

        self.series_var = tk.StringVar()

        self.series_label = tk.Label(row_frame3, text="Select Series:")

        self.series_dropdown = tk.OptionMenu(
            row_frame3,
            self.series_var,
            ""
        )

        # Number in series
        self.num_in_series = tk.Label(row_frame4, text="Book Number:")

        self.num_in_series_entry = tk.Entry(row_frame4, width=20)

        # Hide initially
        self.series_dropdown.pack_forget()
        self.series_label.pack_forget()
        self.num_in_series.pack_forget()

        # Published Date
        self.pub_date = tk.Label(row_frame5, text="Published:")
        self.pub_date.pack(side="left", pady=5)

        self.pub_date_entry = tk.Entry(row_frame5, width=20)
        self.pub_date_entry.pack(side="left", pady=5)

        # NLS Order
        self.nls_num = tk.Label(row_frame6, text="NLS Order#:")
        self.nls_num.pack(side="left", pady=5)

        self.nls_num_entry = tk.Entry(row_frame6, width=20)
        self.nls_num_entry.pack(side="left", pady=5)

        # Save button
        tk.Button(
            self,
            text="Add Book",
            command=self.save_book
        ).pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def save_book(self):

        title = self.title_entry.get().strip()
        author_name = self.selected_author.get()
        selected_series = self.series_var.get()

        if not selected_series:
            series_id = None
        else:
            series_id = self.series_map[selected_series]

        book_num = self.num_in_series_entry.get()
        pub_date = self.pub_date_entry.get()
        nls_num = self.nls_num_entry.get()

        if not title:
            messagebox.showerror("Error", "Book title required")
            return

        if not author_name:
            messagebox.showerror("Error", "Select an author")
            return
        # print(type(series_id), " series id: " + series_id)



        author_id = self.author_map[author_name]
        db_add.add_book(title, author_id, series_id, book_num, pub_date, nls_num)

        messagebox.showinfo("Success", "Book added!")
        self.parent.load_books()
        self.on_close()

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
            self.series_dropdown.pack_forget()
            self.series_label.pack_forget()
            self.num_in_series.pack_forget()
            self.num_in_series_entry.pack_forget()
        else:
            # Show dropdown only AFTER author selected
            self.series_label.pack(side="left", pady=5)
            self.series_dropdown.pack(side="left", pady=5)
            self.num_in_series.pack(side="left", pady=5)
            self.num_in_series_entry.pack(side="left")

        # Set default value
        if series:
            self.series_var.set(series[0][1])

    def on_close(self):
        self.parent.add_book_window = None
        self.destroy()