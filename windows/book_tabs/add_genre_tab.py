import tkinter as tk

from db import db_add


class GenreTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        tk.Label(self, text="Genre Name:").grid(row=0, column=0, sticky="e")
        self.genre = tk.Entry(self, width=20)
        self.genre.grid(row=0, column=1, sticky="w")

        self.error_label = tk.Label(self, text="", fg="red")
        self.success_label = tk.Label(self, text="Genre Successfully Added!", fg="green")

        tk.Button(
            self,
            text="Add Genre",
            command=self.add_genre
        ).grid(row=3, column=1)

    def add_genre(self):
        self.error_label.grid_forget()
        self.success_label.grid_forget()

        genre_name = self.genre.get().strip()

        if not genre_name:
            self.genre.config(bg="#FF9999", fg="black")
            self.error_label.config(text="Genre title must not be empty!")
            self.error_label.grid(row=1, column=1)
            return
        data = (genre_name, )
        db_attempt = db_add.add_genre(data)
        if db_attempt == "success":
            self.genre.delete(0, tk.END)
            self.genre.config(bg='SystemButtonFace')

            self.success_label.grid(row=2, column=1)
        else:
            self.error_label.config(text=f"Error: {db_attempt}!", fg="red")
            self.error_label.grid(row=2, column=1)
        self.genre.delete(0, tk.END)
