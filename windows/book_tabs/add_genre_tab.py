import tkinter as tk
import customtkinter as ctk
from CTkColorPicker import *

from db import db_add


class GenreTab(tk.Frame):
    def __init__(self, parent, app, window):
        super().__init__(parent)

        self.app = app
        self.window = window
        self.style = {
            "width": 200,
            "border_color": "gray40"
        }

        tk.Label(self, text="Genre Name:").grid(row=0, column=0, sticky="e", pady=2)
        self.genre = ctk.CTkEntry(self, **self.style)
        self.genre.grid(row=0, column=1, sticky="w", pady=2)

        tk.Label(self, text="Genre Color:").grid(row=1, column=0, sticky="e", pady=2)
        self.genre_color_picker = ctk.CTkEntry(self, **self.style)
        self.genre_color_picker.grid(row=1, column=1, sticky="w", pady=2)

        colorpicker = CTkColorPicker(self, width=150, command=lambda e: self.set_color(e))
        colorpicker.grid(row=2, column=1, pady=2)

        self.error_label = tk.Label(self, text="", fg="red")
        self.success_label = tk.Label(self, text="Genre Successfully Added!", fg="green")

        ctk.CTkButton(
            self,
            text="Add Genre",
            command=self.add_genre
        ).grid(row=5, column=1, pady=2)

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
            self.error_label.config(text="Genre title must not be empty!")
            self.error_label.grid(row=4, column=1)
            return
        data = (genre_name, genre_color)
        db_attempt = db_add.add_genre(data)
        if db_attempt == "success":
            self.genre.delete(0, tk.END)
            self.genre.configure(**self.style)

            self.success_label.grid(row=4, column=1)
            self.window.refresh_book_tab_genre()
        else:
            self.error_label.config(text=f"Error: {db_attempt}!", fg="red")
            self.error_label.grid(row=4, column=1)
        self.genre.delete(0, tk.END)
