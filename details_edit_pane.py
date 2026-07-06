import customtkinter as ctk
import requests
import PIL.Image as Image
from io import BytesIO

from PIL import ImageTk

from db import db_get


class DetailsEditPane(ctk.CTkFrame):
    def __init__(self, parent, par, app, data):
        super().__init__(parent)
        self.parent = parent
        self.par = par
        self.app = app
        self.book = data

        bar = ctk.CTkFrame(self, border_color="blue", border_width=1)
        bar.pack(side="top", anchor="n", fill="x", expand=True)
        bar.columnconfigure(1, weight=1)

        details = ctk.CTkFrame(self, border_color="red", border_width=1)
        details.pack(side="top", anchor="n", fill="x", expand=True)
        details.columnconfigure(0, weight=1, uniform="group1")
        details.columnconfigure(1, weight=1, uniform="group1")

        col1 = ctk.CTkFrame(details, border_color="blue", border_width=1)
        col1.grid(row=0, column=0, sticky="nsew")
        col2 = ctk.CTkFrame(details, border_color="blue", border_width=1)
        col2.grid(row=0, column=1, sticky="nsew")

        close_img = Image.open('assets/img/close_btn.png').convert('RGBA')
        close_img = close_img.resize((20, 20))
        close_img_display = ImageTk.PhotoImage(close_img)

        self.edit_btn = ctk.CTkButton(bar, text="SAVE", width=50, command=lambda: self.par.load_book(self.book[0]))
        self.edit_btn.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        close_btn = ctk.CTkButton(bar, image=close_img_display, text=None, width=20, fg_color="transparent", command=self.app.close_book)
        close_btn.image = close_img_display
        close_btn.grid(row=0, column=1, sticky="e", padx=5, pady=2)

        # Title
        ctk.CTkLabel(col1, text="Title:").grid(row=0, column=0, sticky="e", padx=2)
        title_entry = ctk.CTkEntry(col1)
        title_entry.grid(row=0, column=1, sticky="w", padx=5)
        title_entry.insert(0, self.book[1])

        # Author
        ctk.CTkLabel(col1, text="Author:").grid(row=1, column=0, sticky="e", padx=2)
        title_entry = ctk.CTkEntry(col1)
        title_entry.grid(row=1, column=1, sticky="w", padx=5)
        title_entry.insert(0, self.book[5])

        # Series
        ctk.CTkLabel(col1, text="Title:").grid(row=2, column=0, sticky="e", padx=2)
        title_entry = ctk.CTkEntry(col1)
        title_entry.grid(row=2, column=1, sticky="w", padx=5)
        title_entry.insert(0, self.book[2])

