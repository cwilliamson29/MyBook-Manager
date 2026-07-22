import tkinter as tk
import customtkinter as ctk

from db import db_add, db_get


class TopicsTab(tk.Frame):

    def __init__(self, parent, app, window):
        super().__init__(parent)

        self.app = app
        self.window = window

        self.style = {
            "width": 200,
            "border_color": "gray40",
            "border_width": 1,
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="e", pady=2)
        self.name = ctk.CTkEntry(self, **self.style)
        self.name.grid(row=0, column=1, sticky="w", pady=2)

        self.error_label = tk.Label(self, text="", fg="red")
        self.success_label = tk.Label(self, text="Genre Successfully Added!", fg="green")

        ctk.CTkButton(
            self,
            text="Add Topic",
            command=self.add_topic
        ).grid(row=2, column=1, pady=2)

    def add_topic(self):
        self.error_label.grid_forget()
        self.success_label.grid_forget()

        topic_name = self.name.get().strip()

        if not topic_name:
            self.name.configure(border_color="red")
            self.error_label.config(text="Topic name must not be empty!")
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
            self.error_label.config(text=f"Error: {db_attempt}!", fg="red")
            self.error_label.grid(row=1, column=1)
        self.name.delete(0, tk.END)