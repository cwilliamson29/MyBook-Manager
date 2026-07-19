import tkinter as tk
import customtkinter as ctk

from db import db_add, db_get


class SeriesTab(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.style = {
            "width": 200,
            "border_color": "gray40",
            "border_width": 1,
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        tk.Label(self, text="Title:").grid(row=0, column=0, sticky="e", pady=2)
        self.title = ctk.CTkEntry(self, **self.style)
        self.title.grid(row=0, column=1, sticky="w", pady=2)

        # Load authors
        self.authors = db_get.get_authors()

        tk.Label(self, text="Select Author:").grid(row=1, column=0, sticky="e", pady=2)

        self.selected_author = tk.StringVar()

        # map display name -> id
        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }
        self.author_dropdown = ctk.CTkComboBox(
            self,
            values=list(self.author_map.keys()),
            variable=self.selected_author,
            **self.style
        )
        self.author_dropdown.grid(row=1, column=1, sticky="w", pady=2)

        self.error_label = tk.Label(self, text="", fg="red")
        self.success_label = tk.Label(self, text="Author Successfully Added!", fg="green")


        ctk.CTkButton(
            self,
            text="Add Series",
            command=self.add_series
        ).grid(row=3, column=1, pady=2)

    def add_series(self):
        self.error_label.grid_forget()
        self.success_label.grid_forget()

        self.title.configure(** self.style)
        self.author_dropdown.configure(** self.style)

        title_get = self.title.get().strip()
        author_name = self.selected_author.get()

        if not title_get or not author_name:
            if not title_get:
                self.title.configure(border_color="red")
            if not author_name or author_name == "":
                self.author_dropdown.configure(border_color="red")

            self.error_label.config(text="Title and author required")
            self.error_label.grid(row=2, column=1)
            return

        author_id = self.author_map[author_name]
        data = (title_get,author_id)
        db_attempt = db_add.add_series(data)

        if db_attempt == "success":
            self.title.delete(0, tk.END)
            self.selected_author.set("")
            self.title.configure(**self.style)
            self.author_dropdown.configure(**self.style)

            self.success_label.grid(row=2, column=1)
        else:
            self.error_label.config(text=f"Error: {db_attempt}!", fg="red")
            self.error_label.grid(row=2, column=1)

    def refresh_authors(self):
        self.authors =  db_get.get_authors()
        amap = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }
        self.author_map = amap
        self.author_dropdown.configure(values=list(self.author_map.keys()))