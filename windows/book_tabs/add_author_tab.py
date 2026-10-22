import tkinter as tk
import customtkinter as ctk

from db import db_add

class AuthorTab(ctk.CTkFrame):
    def __init__(self, parent, app, window):
        super().__init__(parent, fg_color="transparent")

        self.app = app
        self.window = window
        self.style = {
            "width": 200,
            "border_color": ("gray70", "gray40"),
            "border_width": 1,
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(self, text="First Name:").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=4)
        self.first = ctk.CTkEntry(self, **self.style)
        self.first.grid(row=0, column=1, sticky="w", pady=4)

        ctk.CTkLabel(self, text="Last Name:").grid(row=1, column=0, sticky="e", padx=(0, 6), pady=4)
        self.last = ctk.CTkEntry(self, **self.style)
        self.last.grid(row=1, column=1, sticky="w", pady=4)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#f85149")
        self.success_label = ctk.CTkLabel(self, text="Author Successfully Added!", text_color="#2ea043")

        ctk.CTkButton(
            self,
            text="Add Author",
            fg_color="#238636",
            hover_color="#2ea043",
            command=self.add_author
        ).grid(row=3, column=1, pady=6)

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

            self.error_label.configure(text="First and last name required")
            self.error_label.grid(row=2, column=1)
            return
        data = (fname, lname)
        db_attempt = db_add.add_author(data)

        if db_attempt[0] == "success":
            self.first.delete(0, tk.END)
            self.last.delete(0, tk.END)
            self.first.configure(**self.style)
            self.last.configure(**self.style)

            self.success_label.grid(row=2, column=1)
            # self.app.get_authors()
            self.window.refresh_book_tab_authors()
            self.window.refresh_series_tab_authors()
        else:
            self.error_label.configure(text=f"Error: {db_attempt}!")
            self.error_label.grid(row=2, column=1)