import tkinter as tk
import customtkinter as ctk
from CTkColorPicker import *

from db import db_add


class GenreTab(ctk.CTkFrame):
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

        ctk.CTkLabel(self, text="Genre Name:").grid(row=0, column=0, sticky="e", padx=(0, 6), pady=4)
        self.genre = ctk.CTkEntry(self, **self.style)
        self.genre.grid(row=0, column=1, sticky="w", pady=4)

        ctk.CTkLabel(self, text="Genre Color:").grid(row=1, column=0, sticky="e", padx=(0, 6), pady=4)
        self.genre_color_picker = ctk.CTkEntry(self, **self.style)
        self.genre_color_picker.grid(row=1, column=1, sticky="w", pady=4)

        colorpicker = CTkColorPicker(self, width=150, command=lambda e: self.set_color(e))
        colorpicker.grid(row=2, column=1, pady=4)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#f85149")
        self.success_label = ctk.CTkLabel(self, text="Genre Successfully Added!", text_color="#2ea043")

        ctk.CTkButton(
            self,
            text="Add Genre",
            fg_color="#238636",
            hover_color="#2ea043",
            command=self.add_genre
        ).grid(row=5, column=1, pady=6)

    def set_color(self, e):
        self.genre_color_picker.delete(0, "end")
        self.genre_color_picker.insert(0, e)

    def add_genre(self):
        self.error_label.grid_forget()
        self.success_label.grid_forget()

        genre_name = self.genre.get().strip()
        genre_color = self.genre_color_picker.get().strip()

        if not genre_name:
            self.genre.configure(border_color="red")
            self.error_label.configure(text="Genre title must not be empty!")
            self.error_label.grid(row=4, column=1)
            return
        data = (genre_name, genre_color)
        db_attempt = db_add.add_genre(data)
        if db_attempt[0] == "success":
            self.genre.delete(0, tk.END)
            self.genre.configure(**self.style)

            self.success_label.grid(row=4, column=1)
            self.window.refresh_book_tab_genre()
        else:
            self.error_label.configure(text=f"Error: {db_attempt}!")
            self.error_label.grid(row=4, column=1)
        self.genre.delete(0, tk.END)
