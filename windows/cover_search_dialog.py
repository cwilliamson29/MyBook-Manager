import io
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image

from db import db_update
from windows.settings_helpers.cover_fetcher import search_covers_by_title_and_author, clean_isbn


class CoverSearchDialog(ctk.CTkToplevel):
    """
    Dialog window allowing users to search online for book cover artwork
    using Title and Author Name (and optional ISBN), preview up to 3 results,
    and choose which cover to save to the database.
    """

    def __init__(self, parent, app, book_id, title="", author="", isbn="", on_cover_selected=None):
        super().__init__(parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent)

        self.withdraw()
        self.parent_frame = parent
        self.app = app
        self.book_id = book_id
        self.initial_title = str(title or "").strip()
        self.initial_author = str(author or "").strip()
        self.initial_isbn = str(isbn or "").strip()
        self.on_cover_selected = on_cover_selected

        self.is_searching = False
        self.search_results = []
        self.preview_images = []  # Keep references to prevent GC

        self.title("Online Cover Art Search")
        self.center_on_parent(app.root, 760, 660)
        self.deiconify()

        # self.center_window(760, 560)
        # self.resizable(True, True)
        # self.minsize(680, 480)

        # Make dialog modal and stay on top
        top_window = self.parent_frame.winfo_toplevel() if hasattr(self.parent_frame, "winfo_toplevel") else self.parent_frame
        self.transient(top_window)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_ui()
        self.deiconify()

        # Automatically start searching if title or author is provided
        if self.initial_title or self.initial_author or self.initial_isbn:
            self.after(100, self.start_search)

    def center_window(self, width, height):
        self.update_idletasks()
        try:
            parent_win = self.parent_frame.winfo_toplevel() if hasattr(self.parent_frame, "winfo_toplevel") else self.parent_frame
            parent_x = parent_win.winfo_x()
            parent_y = parent_win.winfo_y()
            parent_w = parent_win.winfo_width()
            parent_h = parent_win.winfo_height()
            x = parent_x + (parent_w - width) // 2
            y = parent_y + (parent_h - height) // 2
        except Exception:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2

        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        # 1. Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(side="top", fill="x", padx=20, pady=(15, 10))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="📖 Online Cover Art Search",
            font=("Arial", 18, "bold"),
            text_color="lightblue"
        )
        title_lbl.pack(side="top", anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            header_frame,
            text="Search online catalog by Title and Author name to choose your preferred cover art.",
            font=("Arial", 12),
            text_color="gray70"
        )
        subtitle_lbl.pack(side="top", anchor="w", pady=(2, 0))

        # 2. Search Inputs Panel
        search_card = ctk.CTkFrame(self, fg_color="gray25", corner_radius=8, border_width=1, border_color="gray35")
        search_card.pack(side="top", fill="x", padx=20, pady=(0, 10))

        input_grid = ctk.CTkFrame(search_card, fg_color="transparent")
        input_grid.pack(side="top", fill="x", padx=12, pady=10)
        input_grid.columnconfigure(1, weight=3)
        input_grid.columnconfigure(3, weight=2)
        input_grid.columnconfigure(5, weight=1)

        # Title Field
        ctk.CTkLabel(input_grid, text="Title:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.title_entry = ctk.CTkEntry(input_grid, placeholder_text="Book title", height=28, font=("Arial", 12))
        self.title_entry.insert(0, self.initial_title)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=4)
        self.title_entry.bind("<Return>", lambda e: self.start_search())

        # Author Field
        ctk.CTkLabel(input_grid, text="Author:", font=("Arial", 12, "bold")).grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        self.author_entry = ctk.CTkEntry(input_grid, placeholder_text="Author name", height=28, font=("Arial", 12))
        self.author_entry.insert(0, self.initial_author)
        self.author_entry.grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=4)
        self.author_entry.bind("<Return>", lambda e: self.start_search())

        # ISBN Field
        ctk.CTkLabel(input_grid, text="ISBN:", font=("Arial", 12, "bold")).grid(row=0, column=4, sticky="w", padx=(0, 6), pady=4)
        self.isbn_entry = ctk.CTkEntry(input_grid, placeholder_text="Optional ISBN", height=28, font=("Arial", 12))
        self.isbn_entry.insert(0, self.initial_isbn)
        self.isbn_entry.grid(row=0, column=5, sticky="ew", padx=(0, 12), pady=4)
        self.isbn_entry.bind("<Return>", lambda e: self.start_search())

        # Search Button
        self.search_btn = ctk.CTkButton(
            input_grid,
            text="🔍 Search",
            width=90,
            height=28,
            font=("Arial", 12, "bold"),
            fg_color="#1f6feb",
            hover_color="#388bfd",
            command=self.start_search
        )
        self.search_btn.grid(row=0, column=6, sticky="e", padx=(0, 0), pady=4)

        # 3. Status and Progress Bar
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(side="top", fill="x", padx=20, pady=(0, 6))

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready to search.",
            font=("Arial", 12),
            text_color="gray80"
        )
        self.status_label.pack(side="left", anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=140, height=8, mode="indeterminate")
        # Hidden initially

        # 4. Results Display Area
        self.results_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="gray20",
            corner_radius=8,
            border_width=1,
            border_color="gray30"
        )
        self.results_scroll.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 10))

        # Placeholder message inside results container
        self.empty_label = ctk.CTkLabel(
            self.results_scroll,
            text="Enter book title and author above, then click Search to view cover choices.",
            font=("Arial", 13),
            text_color="gray60"
        )
        self.empty_label.pack(side="top", pady=60)

        # 5. Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(side="bottom", fill="x", padx=20, pady=(0, 12))

        self.close_btn = ctk.CTkButton(
            bottom_bar,
            text="Cancel",
            width=90,
            height=30,
            font=("Arial", 12),
            fg_color="gray40",
            hover_color="gray50",
            command=self.on_close
        )
        self.close_btn.pack(side="right")

    def start_search(self):
        """Initiates online search in a background thread."""
        if self.is_searching:
            return

        title_query = self.title_entry.get().strip()
        author_query = self.author_entry.get().strip()
        isbn_query = self.isbn_entry.get().strip()

        if not title_query and not author_query and not isbn_query:
            self.status_label.configure(text="Please enter a book title, author, or ISBN to search.")
            return

        self.is_searching = True
        self.search_btn.configure(text="Searching...", state="disabled")
        self.status_label.configure(text="Searching Open Library & Google Books for cover art...")
        self.progress_bar.pack(side="right", padx=(10, 0))
        self.progress_bar.start()

        # Clear existing result cards
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        loading_lbl = ctk.CTkLabel(
            self.results_scroll,
            text="⏳ Searching online catalogs and downloading cover images...",
            font=("Arial", 13),
            text_color="lightblue"
        )
        loading_lbl.pack(side="top", pady=60)

        def _bg_worker():
            try:
                results = search_covers_by_title_and_author(
                    title=title_query,
                    author=author_query,
                    isbn=isbn_query,
                    max_results=3,
                    timeout=8
                )
            except Exception as e:
                print("Cover search exception:", e)
                results = []

            if self.winfo_exists():
                self.after(0, lambda: self._on_search_finish(results))

        threading.Thread(target=_bg_worker, daemon=True).start()

    def _on_search_finish(self, results):
        if not self.winfo_exists():
            return

        self.is_searching = False
        self.search_btn.configure(text="🔍 Search", state="normal")
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

        self.search_results = results
        self.preview_images.clear()

        # Clear loading label
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        if not results:
            self.status_label.configure(
                text="No cover art found. Try modifying the title/author name or enter an ISBN.",
                text_color="#f85149"
            )
            empty_lbl = ctk.CTkLabel(
                self.results_scroll,
                text="❌ No cover artwork found online for this query.\n\nYou can refine the search terms above or upload an image manually.",
                font=("Arial", 13),
                text_color="gray70",
                justify="center"
            )
            empty_lbl.pack(side="top", pady=50)
            return

        count = len(results)
        if count == 1:
            self.status_label.configure(
                text="Found 1 matching cover artwork. Click 'Use This Cover' to select it:",
                text_color="#2ea043"
            )
        else:
            self.status_label.configure(
                text=f"Found {count} cover artwork options. Choose which one to use:",
                text_color="#2ea043"
            )

        # Create cards container
        cards_frame = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
        cards_frame.pack(side="top", fill="both", expand=True, padx=4, pady=4)

        for col_idx in range(count):
            cards_frame.columnconfigure(col_idx, weight=1, uniform="card")

        # Build up to 3 cards
        for idx, item in enumerate(results):
            self._render_result_card(cards_frame, item, idx)

    def _render_result_card(self, parent, item, col_idx):
        card = ctk.CTkFrame(
            parent,
            fg_color="gray25",
            corner_radius=8,
            border_width=1,
            border_color="gray35"
        )
        card.grid(row=0, column=col_idx, sticky="nsew", padx=6, pady=4)

        # Convert image bytes to CTkImage
        try:
            pil_img = Image.open(io.BytesIO(item["image_bytes"]))
            img_copy = pil_img.copy()
            if img_copy.mode not in ("RGB", "RGBA"):
                img_copy = img_copy.convert("RGBA")
            img_copy.thumbnail((140, 190), Image.Resampling.LANCZOS)
            w, h = max(img_copy.size[0], 1), max(img_copy.size[1], 1)
            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(w, h))
            self.preview_images.append(ctk_img)

            img_label = ctk.CTkLabel(card, image=ctk_img, text="", cursor="hand2")
            img_label.pack(side="top", padx=10, pady=(10, 6))
            img_label.bind("<Button-1>", lambda e, it=item: self.select_cover(it))
        except Exception as e:
            print("Error rendering cover thumbnail:", e)
            img_label = ctk.CTkLabel(card, text="[No Preview]", height=180)
            img_label.pack(side="top", padx=10, pady=(10, 6))

        # Title Label
        display_title = item.get("title") or "Unknown Title"
        if len(display_title) > 36:
            display_title = display_title[:33] + "..."
        title_lbl = ctk.CTkLabel(
            card,
            text=display_title,
            font=("Arial", 11, "bold"),
            wraplength=190,
            justify="center"
        )
        title_lbl.pack(side="top", padx=8, pady=(0, 2))

        # Author Label
        display_author = item.get("author") or ""
        if len(display_author) > 32:
            display_author = display_author[:29] + "..."
        if display_author:
            author_lbl = ctk.CTkLabel(
                card,
                text=display_author,
                font=("Arial", 10),
                text_color="gray80",
                wraplength=190,
                justify="center"
            )
            author_lbl.pack(side="top", padx=8, pady=(0, 2))

        # Source / Year Label
        meta_parts = []
        if item.get("year"):
            meta_parts.append(str(item["year"]))
        if item.get("source"):
            meta_parts.append(str(item["source"]))
        meta_text = " • ".join(meta_parts)
        if meta_text:
            meta_lbl = ctk.CTkLabel(
                card,
                text=meta_text,
                font=("Arial", 9, "italic"),
                text_color="gray60"
            )
            meta_lbl.pack(side="top", padx=8, pady=(0, 2))

        # ISBN Badge / Label
        item_isbn = item.get("isbn")
        if item_isbn:
            isbn_lbl = ctk.CTkLabel(
                card,
                text=f"ISBN: {item_isbn}",
                font=("Arial", 10, "bold"),
                text_color="lightblue"
            )
            isbn_lbl.pack(side="top", padx=8, pady=(0, 4))

        # Select Button
        select_btn = ctk.CTkButton(
            card,
            text=f"Use Cover #{col_idx + 1}" if len(self.search_results) > 1 else "Use This Cover",
            height=28,
            font=("Arial", 11, "bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            command=lambda it=item: self.select_cover(it)
        )
        select_btn.pack(side="bottom", fill="x", padx=12, pady=(4, 10))

    def select_cover(self, item):
        """Saves selected cover bytes to database, auto-updates ISBN if found, and updates parent UI."""
        if not self.book_id:
            return

        try:
            image_bytes = item.get("image_bytes")
            if not image_bytes:
                messagebox.showerror("Error", "Invalid image data.")
                return

            res = db_update.update_book_cover(self.book_id, image_bytes)
            if res != "success":
                messagebox.showerror("Error", f"Failed to save cover image to database: {res}")
                return

            # Auto-update ISBN in the database if an ISBN is present in the chosen search result or dialog entry
            item_isbn = item.get("isbn")
            entry_isbn = self.isbn_entry.get().strip() if hasattr(self, "isbn_entry") else ""
            isbn_to_save = item_isbn or entry_isbn
            if isbn_to_save:
                clean_code = clean_isbn(isbn_to_save)
                if clean_code:
                    db_update.update_book_isbn(self.book_id, clean_code)

            if self.on_cover_selected:
                try:
                    self.on_cover_selected(self.book_id)
                except Exception as e:
                    print("Error in on_cover_selected callback:", e)
            self.on_close()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving cover image: {e}")

    def on_close(self):
        self.grab_release()
        self.destroy()

    def center_on_parent(self, parent, width, height):
        parent.update_idletasks()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")