import tkinter as tk

from db import db_add


class AuthorTab(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        tk.Label(self, text="First Name").grid(row=0, column=0, sticky="e")
        self.first = tk.Entry(self, width=20)
        self.first.grid(row=0, column=1, sticky="w")

        tk.Label(self, text="Last Name").grid(row=1, column=0, sticky="e")
        self.last = tk.Entry(self, width=20)
        self.last.grid(row=1, column=1, sticky="w")

        tk.Button(
            self,
            text="Add Author",
            command=self.add_author
        ).grid(row=2, column=1)

    def add_author(self):

        first = self.first.get().strip()
        last = self.last.get().strip()

        if not first or not last:
            return

        db_add.add_author(first, last)

        self.first.delete(0, tk.END)
        self.last.delete(0, tk.END)