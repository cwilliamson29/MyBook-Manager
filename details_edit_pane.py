import customtkinter as ctk
import requests
import PIL.Image as Image
from io import BytesIO

from PIL import ImageTk

from db import db_get


class DetailsEditPane(ctk.CTkFrame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.parent = parent
        self.book = data

        ctk.CTkLabel(self, text="Title:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        title_entry = ctk.CTkEntry(self)
        title_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        title_entry.insert(0, self.book[1])

        