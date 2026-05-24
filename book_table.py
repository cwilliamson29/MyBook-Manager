import tkinter as tk
from tkinter import ttk, messagebox
from db import database
from windows.edit_book_window import EditBookWindow


class BookTable(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=("Arial", 12), borderwidth=5, relief="solid")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), borderwidth=5, relief="solid", border_width=5)

        # Treeview
        self.tree = ttk.Treeview(
            self,
            columns=("Edit", "Delete", "Book #", "Series", "Title", "Author", "Rating", "Genre", "ISBN","NLS Order"),
            show="headings",
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(command=self.tree.yview)

        # Headings
        self.tree.heading("Edit", text="Edit", anchor="center")
        self.tree.heading("Delete", text="Delete", anchor="center")
        self.tree.heading("Book #", text="Book #")
        self.tree.heading("Series", text="Series")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Author", text="Author")
        self.tree.heading("Rating", text="Rating")
        self.tree.heading("Genre", text="Genre")
        self.tree.heading("ISBN", text="ISBN")
        self.tree.heading("NLS Order", text="NLS Order")

        # Column sizes
        self.tree.column("Edit", width=50, stretch=False)
        self.tree.column("Delete", width=50, stretch=False)
        self.tree.column("Book #", width=50, stretch=False)
        self.tree.column("Series", width=200)
        self.tree.column("Title", width=300)
        self.tree.column("Author", width=150)
        self.tree.column("Rating", width=50, stretch=False)
        self.tree.column("Genre", width=100, stretch=False)
        self.tree.column("ISBN", width=130, stretch=False)
        self.tree.column("NLS Order", width=150)

        self.tree.tag_configure("oddrow", background="#cccccc", foreground="black")
        self.tree.tag_configure("evenrow", background="white", foreground="black")

        self.tree.bind("<Button-1>", self.on_click)

        self.tree.pack(fill="both", expand=True, pady=2)

    def load_books(self):

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get books from database
        books = database.get_books()

        # print(books)

        self.populate_table(books)


    def populate_table(self, books):

        # clear old rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # insert new rows
        for index, book in enumerate(books):
            tag = "evenrow" if index % 2 == 0 else "oddrow"

            book_id = book[0]
            title = book[1]
            series = book[2]
            book_number = book[3]
            author = f"{book[4]} {book[5]}"
            rating = "50"
            genre = "Sci-Fi"
            isbn = "asdf2345asdf2"
            nls_order = book[7]

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
                values=("✏️", "🗑️", book_number, series, title, author, rating, genre, isbn, nls_order),
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
        # EDIT COLUMN
        # ====================================

        if column == "#1":
            self.edit_book(book_id)

        # ====================================
        # DELETE COLUMN
        # ====================================

        elif column == "#2":
            self.delete_book(book_id)

    # ========================================
    # EDIT BOOK
    # ========================================

    def edit_book(self, book_id):

        # print(f"Edit book: {book_id}")

        # Replace with your edit window
        # Example:
        #
        EditBookWindow(self, book_id)

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
        database.delete_book(book_id)

        # Reload table
        books = database.get_books()

        self.populate_table(books)