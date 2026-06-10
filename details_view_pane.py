import customtkinter as ctk
import requests
import PIL.Image as Image
from io import BytesIO

from PIL import ImageTk

from db import db_get


class DetailsViewPane(ctk.CTkFrame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.parent = parent
        self.book = data


        # Title
        ctk.CTkLabel(self, text="Title:").grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.title_value = ctk.CTkLabel(self, text=self.book[1])
        self.title_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # Author
        ctk.CTkLabel(self, text="Author:").grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.author_value = ctk.CTkLabel(self, text=self.book[4])
        self.author_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Series
        ctk.CTkLabel(self, text="Series:").grid(row=2, column=0, sticky="w", padx=5, pady=2)

        self.series_value = ctk.CTkLabel(self, text=self.book[2])
        self.series_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # ISBN
        ctk.CTkLabel(self, text="ISBN:").grid(row=3, column=0, sticky="w", padx=5, pady=2)

        self.isbn_value = ctk.CTkLabel(self, text=self.book[8])
        self.isbn_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
