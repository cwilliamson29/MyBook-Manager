import customtkinter as ctk
import requests
import PIL.Image as Image
from io import BytesIO

from db import db_get


class DetailsFrame(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.grid_columnconfigure(3, weight=1)

        left_frame = ctk.CTkFrame(self, border_color="white")
        left_frame.grid(row=0, column=0, sticky="s")
        center_frame = ctk.CTkFrame(self, border_color="blue")
        center_frame.grid(row=0, column=1, sticky="e")
        right_frame = ctk.CTkFrame(self, border_color="red")
        right_frame.grid(row=0, column=2, sticky="e")


        imgurl = "https://imgs.search.brave.com/1o7gEYxi0RYNcwVdUp-a8-XrKWyN8K95j1aquBuXgHs/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9jZG4u/aWNvbnNjb3V0LmNv/bS9pY29uL3ByZW1p/dW0vcG5nLTI1Ni10/aHVtYi9waWN0dXJl/LWljb24tc3ZnLWRv/d25sb2FkLXBuZy0x/MTYxOTAwOS5wbmc_/Zj13ZWJwJnc9MTI4"
        img = self.load_image_from_url(imgurl)
        ctk_img = ctk.CTkImage(img, img, (200,200))

        ctk.CTkLabel(left_frame, image=ctk_img).grid(row=0, column=0, sticky="w", padx=5, pady=2)

        # Title
        ctk.CTkLabel(center_frame,text="Title:").grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.title_value = ctk.CTkLabel(self, text="")
        self.title_value.grid(row=0,column=1,sticky="w",padx=5, pady=2)

        # Author
        ctk.CTkLabel(self,text="Author:").grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.author_value = ctk.CTkLabel(self, text="")
        self.author_value.grid(row=1,column=1, sticky="w",padx=5,pady=2)

        # Series
        ctk.CTkLabel(self,text="Series:").grid(row=2, column=0, sticky="w", padx=5, pady=2)

        self.series_value = ctk.CTkLabel(self,text="")
        self.series_value.grid(row=2,column=1,sticky="w",padx=5, pady=2)

        # ISBN
        ctk.CTkLabel(self,text="ISBN:").grid(row=3, column=0, sticky="w", padx=5, pady=2)

        self.isbn_value = ctk.CTkLabel(self,text="")
        self.isbn_value.grid(row=3,column=1,sticky="w",padx=5,pady=2)

    def load_book(self, book_id):
        book = db_get.get_book_by_id(book_id)

        print(book)
        self.title_value.configure(
            text=book[0][1]
        )

        self.author_value.configure(
            text=book[0][4] + " " + book[0][5]
        )

        self.series_value.configure(
            text=book[0][2] or "Standalone"
        )

        self.isbn_value.configure(
            text=book[0][8]
        )

    def load_image_from_url(self, url):
        """Fetches image from URL and returns a PIL Image object."""
        response = requests.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))