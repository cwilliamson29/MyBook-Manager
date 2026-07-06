import customtkinter as ctk
import requests
import PIL.Image as Image
from io import BytesIO

from PIL import ImageTk

from db import db_get


class DetailsViewPane(ctk.CTkFrame):
    def __init__(self, parent, par, app, data):
        super().__init__(parent)
        self.parent = parent
        self.par = par
        self.app = app
        self.book = data

        #### Print book for positions
        print(self.book)

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

        self.edit_btn = ctk.CTkButton(bar, text="EDIT", width=50, command=lambda: self.par.edit_book(self.book[0]))
        self.edit_btn.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        close_btn = ctk.CTkButton(bar, image=close_img_display, text=None, width=20, fg_color="transparent", command=self.app.close_book)
        close_btn.image = close_img_display
        close_btn.grid(row=0, column=1, sticky="e", padx=5, pady=2)

        pady = 0
        padx = 2
        # Title
        ctk.CTkLabel(col1, text="Title:").grid(row=0, column=0, sticky="w", padx=padx)

        self.title_value = ctk.CTkLabel(col1, text=self.book[1])
        self.title_value.grid(row=0, column=1, sticky="w", padx=padx)

        # Author
        ctk.CTkLabel(col1, text="Author:").grid(row=1, column=0, sticky="w", padx=padx, pady=pady)

        self.author_value = ctk.CTkLabel(col1, text=self.book[4] + " " + self.book[5])
        self.author_value.grid(row=1, column=1, sticky="w", padx=padx, pady=pady)

        # Series
        ctk.CTkLabel(col1, text="Series:").grid(row=2, column=0, sticky="w", padx=padx, pady=pady)

        self.series_value = ctk.CTkLabel(col1, text=self.book[2])
        self.series_value.grid(row=2, column=1, sticky="w", padx=padx, pady=pady)

        # Book number
        ctk.CTkLabel(col1, text="Book #:").grid(row=3, column=0, sticky="w", padx=padx, pady=pady)

        self.book_num = ctk.CTkLabel(col1, text=self.book[3])
        self.book_num.grid(row=3, column=1, sticky="w", padx=padx, pady=pady)

        # Genre
        ctk.CTkLabel(col1, text="Genre:").grid(row=4, column=0, sticky="w", padx=padx, pady=pady)

        self.genre = ctk.CTkLabel(col1, text=self.book[7])
        self.genre.grid(row=4, column=1, sticky="w", padx=padx, pady=pady)

        # ISBN
        ctk.CTkLabel(col1, text="ISBN:").grid(row=5, column=0, sticky="w", padx=padx, pady=pady)

        self.isbn_value = ctk.CTkLabel(col1, text=self.book[8])
        self.isbn_value.grid(row=5, column=1, sticky="w", padx=padx, pady=pady)

        # Rating
        ctk.CTkLabel(col2, text="Rating:").grid(row=0, column=0, sticky="w", padx=padx, pady=pady)

        self.isbn_value = ctk.CTkLabel(col2, text=self.book[6])
        self.isbn_value.grid(row=0, column=1, sticky="w", padx=padx, pady=pady)

        # NLS ORder
        ctk.CTkLabel(col2, text="NLS Order:").grid(row=1, column=0, sticky="w", padx=padx, pady=pady)

        self.isbn_value = ctk.CTkLabel(col2, text=self.book[9])
        self.isbn_value.grid(row=1, column=1, sticky="w", padx=padx, pady=pady)

        # Description
        ctk.CTkLabel(col2, text="Description:").grid(row=2, column=0, sticky="w", padx=padx, pady=pady)

        self.isbn_value = ctk.CTkLabel(col2, text=self.book[10])
        self.isbn_value.grid(row=2, column=1, sticky="w", padx=padx, pady=pady)
