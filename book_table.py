import tkinter as tk
from tkinter import ttk, messagebox
from db import db_get, db_update


class BookTable(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.parent = parent
        self.app = app

        # Scrollbar
        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=("Arial", 12), borderwidth=5, relief="solid")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), borderwidth=5, relief="solid", border_width=5)

        # Treeview
        self.tree = ttk.Treeview(
            self,
            columns=("Delete", "Book #", "Series", "Title", "Author", "Rating", "Genre", "Topics", "ISBN","NLS Order"),
            show="headings",
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(command=self.tree.yview)

        # Headings
        self.tree.heading("Delete", text="🗑️", anchor="center")
        self.tree.heading("Book #", text="Book #")
        self.tree.heading("Series", text="Series")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Author", text="Author")
        self.tree.heading("Rating", text="Rating")
        self.tree.heading("Genre", text="Genre")
        self.tree.heading("Topics", text="Topics")
        self.tree.heading("ISBN", text="ISBN")
        self.tree.heading("NLS Order", text="NLS Order")

        # Column sizes
        self.tree.column("Delete", width=26, stretch=False)
        self.tree.column("Book #", width=50, stretch=False)
        self.tree.column("Series", width=125)
        self.tree.column("Title", width=300)
        self.tree.column("Author", width=75)
        self.tree.column("Rating", width=50, stretch=False)
        self.tree.column("Genre", width=100, stretch=False)
        self.tree.column("Topics", width=180, stretch=False)
        self.tree.column("ISBN", width=100, stretch=False)
        self.tree.column("NLS Order", width=100)

        self.genre_tags ={}

        self.tree.bind("<Button-1>", self.on_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_book_selected)

        self.tree.pack(fill="both", expand=True, pady=2)

    def load_books(self):

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get books from database
        books = db_get.get_books()

        # print(books)

        self.populate_table(books)


    def populate_table(self, books):
        self.tree.tag_configure("oddrow", background="#cccccc", foreground="black")
        self.tree.tag_configure("evenrow", background="white", foreground="black")
        # Genre Tags
        self.genre_tags = db_get.get_genres()
        for genre in self.genre_tags:
            if genre[2] is not None:
                self.tree.tag_configure(genre[1], background=genre[2], foreground="black")
        # clear old rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # insert new rows
        for index, book in enumerate(books):
            topics = db_get.get_book_topics_names(book[0])
            tag = ""
            genre_color_tag = db_get.get_genres_by_title(book[7])

            if genre_color_tag[0][2] is not None:
                tag = genre_color_tag[0][1]
            else:
                tag = "evenrow" if index % 2 == 0 else "oddrow"

            book_id = book[0]
            title = book[1]
            series = book[2]
            book_number = book[3]
            author = f"{book[4]} {book[5]}"
            rating = book[6]
            genre = book[7]
            isbn = book[8]
            topic_names = ", ".join(topics)
            max_length = 20

            if len(topic_names) > max_length:
                topic_names = topic_names[:max_length - 3] + "  ..."

            nls_order = book[9]

            if series is None:
                series = ''
            if book_number is None:
                book_number = ''
            if nls_order is None:
                nls_order = ''

            self.tree.insert(
                "",
                "end",
                iid=str(book_id),
                values=("🗑️", book_number, series, title, author, rating, genre, topic_names, isbn, nls_order),
                tags=(tag,)
            )

    # ========================================
    # HANDLE CLICKS
    # ========================================

    def on_click(self, event):

        # Identify clicked region
        region = self.tree.identify(
            "region",
            event.x,
            event.y
        )

        if region != "cell":
            return

        # Get clicked column + row
        column = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)

        if not row_id:
            return

        # Convert row id back to DB id
        book_id = int(row_id)

        # ====================================
        # DELETE COLUMN
        # ====================================

        if column == "#1":
            self.delete_book(book_id)

    # ========================================
    # DELETE BOOK
    # ========================================

    def delete_book(self, book_id):

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Delete this book?"
        )

        if not confirm:
            return

        # Delete from database
        db_update.delete_book(book_id)

        # Reload table
        books = db_get.get_books()

        self.populate_table(books)

    def on_book_selected(self, event):

        selected = self.tree.selection()

        if not selected:
            return

        book_id = int(selected[0])

        # book = get_book_details(book_id)

        # self.parent.book_details.load_book(book_id)
        # self.parent.details_frame.load_book(book_id)
        # print("here: ")
        # print(hasattr(self.app, "details_frame"))
        # print(type(self.app.details))
        self.app.show_book_details(book_id)