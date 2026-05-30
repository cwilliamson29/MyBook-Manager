import tkinter as tk

from db import db_add, db_get


class SeriesTab(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        tk.Label(self, text="Title").grid(row=0, column=0, sticky="e")
        self.title = tk.Entry(self, width=20)
        self.title.grid(row=0, column=1, sticky="w")

        # Load authors
        self.authors = db_get.get_authors()

        tk.Label(self, text="Select Author").grid(row=1, column=0, sticky="e")

        self.selected_author = tk.StringVar()

        # map display name -> id
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

        tk.Button(
            self,
            text="Add Series",
            command=self.add_series
        ).grid(row=2, column=1)

    def add_series(self):

        title_get = self.title.get().strip()
        author_name = self.selected_author.get()

        if not title_get or not author_name:
            if not title_get:
                self.title.config(bg="#FF9999", fg="black")
            if not author_name or author_name == "":
                self.dropdown.config(bg="#FF9999", fg="black")
            return

        author_id = self.author_map[author_name]

        db_add.add_series(title_get,author_id)

        self.title.delete(0, tk.END)
        self.selected_author.set("")