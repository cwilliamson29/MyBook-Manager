import tkinter as tk
from tkinter import filedialog, messagebox
from io import BytesIO
import threading
import customtkinter as ctk
import requests
import PIL.Image as Image
from PIL import ImageTk

from db import db_get, db_update
from windows.settings_helpers.cover_fetcher import auto_fetch_and_save_book_cover, clean_isbn
from details_edit_pane import DetailsEditPane
from details_view_pane import DetailsViewPane
from details_multi_edit_pane import DetailsMultiEditPane


class DetailsFrame(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app

        self.details_pane = None
        self.book_id = None
        self.current_cover_img = None
        self.is_fetching = False

        self.grid_columnconfigure(3, weight=1)

        # Left frame for cover image and upload/remove controls
        self.left_frame = ctk.CTkFrame(self, width=180, fg_color="gray20")
        self.left_frame.pack(side="left", anchor="n", padx=(10, 5), pady=8, expand=False)

        self.center_frame_details = ctk.CTkFrame(self, fg_color="gray20")
        self.center_frame_details.pack(side="left", anchor="n", fill="x", expand=True)

        self.right_frame = ctk.CTkFrame(self, width=20, fg_color="gray20")
        self.right_frame.pack(side="right", anchor="ne")

        # Cover image display label (clickable to upload)
        self.cover_label = ctk.CTkLabel(self.left_frame, text="", cursor="hand2")
        self.cover_label.pack(side="top", padx=5, pady=(2, 4))
        self.cover_label.bind("<Button-1>", lambda event: self.upload_cover())

        # Action buttons row under cover image
        self.cover_btn_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.cover_btn_frame.pack(side="top", fill="x", padx=4, pady=(0, 2))

        self.fetch_btn = ctk.CTkButton(
            self.cover_btn_frame,
            text="Auto Cover",
            width=80,
            height=26,
            font=("Arial", 11, "bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            command=self.fetch_cover_online
        )
        self.fetch_btn.pack(side="left", padx=(0, 3), expand=True)

        self.upload_btn = ctk.CTkButton(
            self.cover_btn_frame,
            text="Upload",
            width=60,
            height=26,
            font=("Arial", 11, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            command=self.upload_cover
        )
        self.upload_btn.pack(side="left", padx=(0, 3), expand=True)

        self.remove_btn = ctk.CTkButton(
            self.cover_btn_frame,
            text="✕",
            width=24,
            height=26,
            font=("Arial", 11, "bold"),
            fg_color="#cf222e",
            hover_color="#f85149",
            command=self.remove_cover
        )

        self.load_default_cover()

    def create_cover_image(self, pil_img, max_width=150, max_height=200):
        """Resizes image keeping aspect ratio and converts to CTkImage."""
        img_copy = pil_img.copy()
        if img_copy.mode not in ("RGB", "RGBA"):
            img_copy = img_copy.convert("RGBA")
        img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        w, h = img_copy.size
        w = max(w, 1)
        h = max(h, 1)
        return ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(w, h))

    def load_default_cover(self):
        """Loads and displays the default fallback book image."""
        try:
            def_book = Image.open('assets/img/default_book.webp')
            self.current_cover_img = self.create_cover_image(def_book)
            self.cover_label.configure(image=self.current_cover_img)
        except Exception as e:
            print("Error loading default book cover:", e)
        self.remove_btn.pack_forget()
        self.upload_btn.configure(text="Upload")

    def load_cover_image(self, book_id):
        """Loads cover image from database for given book_id or shows default."""
        self.book_id = book_id
        if not book_id:
            self.load_default_cover()
            self.cover_btn_frame.pack_forget()
            return

        self.cover_btn_frame.pack(side="top", fill="x", padx=4, pady=(0, 2))
        cover_data = db_get.get_book_cover(book_id)
        if cover_data:
            try:
                pil_img = Image.open(BytesIO(cover_data))
                self.current_cover_img = self.create_cover_image(pil_img)
                self.cover_label.configure(image=self.current_cover_img)
                self.upload_btn.configure(text="Change")
                self.remove_btn.pack(side="left", padx=(0, 0))
                return
            except Exception as e:
                print("Error displaying cover image:", e)

        self.load_default_cover()

    def fetch_cover_online(self):
        """Fetches the book cover image from online APIs using the book's ISBN."""
        if not self.book_id or self.is_fetching:
            return

        book_rows = db_get.get_book_by_id(self.book_id)
        if not book_rows:
            messagebox.showerror("Error", "Book not found.")
            return

        isbn = book_rows[0][10]
        cleaned = clean_isbn(isbn)
        if not cleaned:
            messagebox.showinfo(
                "ISBN Required",
                "This book does not have a valid ISBN recorded in the database.\n\nPlease edit the book details to add an ISBN first."
            )
            return

        self.is_fetching = True
        self.fetch_btn.configure(text="Fetching...", state="disabled")
        self.upload_btn.configure(state="disabled")

        target_book_id = self.book_id

        def _bg_worker():
            success, msg = auto_fetch_and_save_book_cover(target_book_id, cleaned)
            self.after(0, lambda: self._on_fetch_finish(target_book_id, success, msg))

        threading.Thread(target=_bg_worker, daemon=True).start()

    def _on_fetch_finish(self, book_id, success, msg):
        self.is_fetching = False
        self.fetch_btn.configure(text="Auto Cover", state="normal")
        self.upload_btn.configure(state="normal")

        if success:
            if self.book_id == book_id:
                self.load_cover_image(book_id)
        else:
            messagebox.showinfo("Cover Search", msg)

    def upload_cover(self):
        """Prompts user to select an image, validates it, and saves to database."""
        if not self.book_id:
            return

        file_path = filedialog.askopenfilename(
            title="Select Book Cover Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("WebP files", "*.webp"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            return

        try:
            with open(file_path, "rb") as f:
                raw_bytes = f.read()

            # Validate and optimize image size for efficient storage
            with Image.open(BytesIO(raw_bytes)) as pil_img:
                img_copy = pil_img.copy()

            max_dim = 1200
            if img_copy.width > max_dim or img_copy.height > max_dim:
                img_copy.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            out_io = BytesIO()
            if img_copy.mode in ("RGBA", "LA", "P"):
                img_copy.save(out_io, format="PNG", optimize=True)
            else:
                img_copy.convert("RGB").save(out_io, format="JPEG", quality=90, optimize=True)
            saved_bytes = out_io.getvalue()

            res = db_update.update_book_cover(self.book_id, saved_bytes)
            if res == "success":
                self.load_cover_image(self.book_id)
            else:
                messagebox.showerror("Error", f"Failed to save cover image to database: {res}")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid image file: {e}")

    def remove_cover(self):
        """Removes the cover image from database for current book."""
        if not self.book_id:
            return

        if messagebox.askyesno("Remove Cover", "Are you sure you want to remove the cover image for this book?"):
            res = db_update.update_book_cover(self.book_id, None)
            if res == "success":
                self.load_cover_image(self.book_id)
            else:
                messagebox.showerror("Error", f"Failed to remove cover image: {res}")

    def load_book(self, book_id):
        book = db_get.get_book_by_id(book_id)
        self.book_id = book_id

        if self.details_pane is not None:
            self.details_pane.destroy()

        if book:
            self.details_pane = DetailsViewPane(self.center_frame_details, self, self.app, book[0])
            self.details_pane.pack(side="top", anchor="n", fill="x", expand=True)

        self.load_cover_image(book_id)

    def edit_book(self, book_id):
        book = db_get.get_book_by_id(book_id)
        self.book_id = book_id

        if self.details_pane is not None:
            self.details_pane.destroy()

        if book:
            self.details_pane = DetailsEditPane(self.center_frame_details, self, self.app, book[0])
            self.details_pane.pack(side="top", anchor="n", fill="x", expand=True)

        self.load_cover_image(book_id)

    def load_multi_books(self, book_ids):
        self.book_id = None
        if self.details_pane is not None:
            self.details_pane.destroy()

        self.details_pane = DetailsMultiEditPane(self.center_frame_details, self, self.app, book_ids)
        self.details_pane.pack(side="top", anchor="n", fill="x", expand=True)

        self.load_cover_image(None)

    def load_image_from_url(self, url):
        """Fetches image from URL and returns a PIL Image object."""
        response = requests.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))