import tkinter as tk
import customtkinter as ctk

from db import db_add


class AuthorTab(tk.Frame):

    def __init__(self, parent, app, window):
        super().__init__(parent)

        self.app = app
        self.window = window
        self.style = {
            "width": 200,
            "border_color": "gray40",
            "border_width": 1,
        }
        tk.Label(self, text="First Name:").grid(row=0, column=0, sticky="e", pady=2)
        self.first = ctk.CTkEntry(self, **self.style)
        self.first.grid(row=0, column=1, sticky="w", pady=2)

        tk.Label(self, text="Last Name:").grid(row=1, column=0, sticky="e", pady=2)
        self.last = ctk.CTkEntry(self, **self.style)
        self.last.grid(row=1, column=1, sticky="w", pady=2)

        self.error_label = tk.Label(self, text="", fg="red")
        self.success_label = tk.Label(self, text="Author Successfully Added!", fg="green")

        ctk.CTkButton(
            self,
            text="Add Author",
            command=self.add_author
        ).grid(row=3, column=1, pady=2)

    def add_author(self):
        self.error_label.grid_forget()
        self.success_label.grid_forget()

        self.first.configure(**self.style)
        self.last.configure(**self.style)

        fname = self.first.get().strip()
        lname = self.last.get().strip()

        if not fname or not lname:
            if not fname:
                self.first.configure(border_color="red")

            if not lname:
                self.last.configure(border_color="red")

            self.error_label.config(text="First and last name required")
            self.error_label.grid(row=2, column=1)
            return
        data = (fname, lname)
        db_attempt = db_add.add_author(data)

        if db_attempt == "success":
            self.first.delete(0, tk.END)
            self.last.delete(0, tk.END)
            self.first.configure(**self.style)
            self.last.configure(**self.style)

            self.success_label.grid(row=2, column=1)
            # self.app.get_authors()
            self.window.refresh_book_tab_authors()
            self.window.refresh_series_tab_authors()
        else:
            self.error_label.config(text=f"Error: {db_attempt}!", fg="red")
            self.error_label.grid(row=2, column=1)