import tkinter as tk
import customtkinter as ctk

from db import db_add, db_get


class TopicsTab(ctk.CTkFrame):

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

        ctk.CTkLabel(self, text="Name:").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=4)
        self.name = ctk.CTkEntry(self, **self.style)
        self.name.grid(row=0, column=1, sticky="w", pady=4)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#f85149")
        self.success_label = ctk.CTkLabel(self, text="Topic Successfully Added!", text_color="#2ea043")

        ctk.CTkButton(
            self,
            text="Add Topic",
            fg_color="#238636",
            hover_color="#2ea043",
            command=self.add_topic
        ).grid(row=2, column=1, pady=6)

    def add_topic(self):
        self.error_label.grid_forget()
        self.success_label.grid_forget()

        topic_name = self.name.get().strip()

        if not topic_name:
            self.name.configure(border_color="red")
            self.error_label.configure(text="Topic name must not be empty!")
            self.error_label.grid(row=1, column=1)
            return
        data = (topic_name,)
        db_attempt = db_add.add_topic(data)
        if db_attempt[0] == "success":
            self.name.delete(0, tk.END)
            self.name.configure(**self.style)

            self.success_label.grid(row=1, column=1)
            self.window.refresh_book_tab_topics()
        else:
            self.error_label.configure(text=f"Error: {db_attempt}!")
            self.error_label.grid(row=1, column=1)
        self.name.delete(0, tk.END)