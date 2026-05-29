import tkinter as tk

from db import db_add


class GenreTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        tk.Label(self, text="Genre Name:").grid(row=0, column=0, sticky="e")
        self.genre = tk.Entry(self, width=20)
        self.genre.grid(row=0, column=1, sticky="w")

        self.error = tk.Label(self, text="Genre title must not be empty!")
        self.error.grid_forget()

        tk.Button(
            self,
            text="Add Author",
            command=self.add_genre
        ).grid(row=2, column=1)

    def add_genre(self):
        genre_name = self.genre.get().strip()
        # print("The genre is: " + genreTitle)
        # print(type(genreTitle))

        if not genre_name:
            self.error.grid(row=1, column=1, sticky="e")
            return

        db_add.add_genre(genre_name)

        self.genre.delete(0, tk.END)
