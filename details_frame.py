import customtkinter as ctk
import requests
import PIL.Image as Image
from io import BytesIO

from PIL import ImageTk

from db import db_get
from details_edit_pane import DetailsEditPane
from details_view_pane import DetailsViewPane


class DetailsFrame(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app

        self.details_pane = None

        self.book_id = 1

        self.grid_columnconfigure(3, weight=1)

        # left_frame = ctk.CTkFrame(self, border_color="gray40", width=200, border_width=1)
        left_frame = ctk.CTkFrame(self, width=200, fg_color="gray20")
        left_frame.pack(side="left", expand=False)

        # center_frame = ctk.CTkFrame(self, border_color="blue", border_width=1)
        # center_frame = ctk.CTkFrame(self)
        # center_frame.pack(side="left", anchor="n", fill="x", expand=True)

        # self.center_frame_details = ctk.CTkFrame(self, border_color="blue", border_width=1)
        self.center_frame_details = ctk.CTkFrame(self, fg_color="gray20")
        self.center_frame_details.pack(side="left", anchor="n", fill="x", expand=True)

        # right_frame = ctk.CTkFrame(self, border_color="gray40",width=300, border_width=1)
        right_frame = ctk.CTkFrame(self, width=300, fg_color="gray20")
        right_frame.pack(side="right", anchor="ne")

        imgurl = "https://imgs.search.brave.com/1o7gEYxi0RYNcwVdUp-a8-XrKWyN8K95j1aquBuXgHs/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9jZG4u/aWNvbnNjb3V0LmNv/bS9pY29uL3ByZW1p/dW0vcG5nLTI1Ni10/aHVtYi9waWN0dXJl/LWljb24tc3ZnLWRv/d25sb2FkLXBuZy0x/MTYxOTAwOS5wbmc_/Zj13ZWJwJnc9MTI4"
        img = self.load_image_from_url(imgurl)
        ctk_img = ctk.CTkImage(img, img, (225,225))

        ctk.CTkLabel(left_frame, image=ctk_img).grid(row=0, column=0, sticky="w", padx=5, pady=2)

    def load_book(self, book_id):
        book = db_get.get_book_by_id(book_id)
        self.book_id = book_id

        if self.details_pane is not None:
            self.details_pane.destroy()

        self.details_pane = DetailsViewPane(self.center_frame_details, self, self.app, book[0])
        self.details_pane.pack(side="top", anchor="n", fill="x", expand=True)

    def edit_book(self, book_id):
        book = db_get.get_book_by_id(book_id)
        if self.details_pane is not None:
            self.details_pane.destroy()

        self.details_pane = DetailsEditPane(self.center_frame_details, self, self.app, book[0])
        self.details_pane.pack(side="top", anchor="n", fill="x", expand=True)

    def load_image_from_url(self, url):
        """Fetches image from URL and returns a PIL Image object."""
        response = requests.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))