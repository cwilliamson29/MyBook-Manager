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

        # Context menu
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Edit Selected (Genre & Topics)", command=self.edit_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all)
        self.context_menu.add_command(label="Deselect All", command=self.deselect_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Selected", command=self.delete_selected)

        self.tree.bind("<Button-2>", self.show_context_menu)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Control-Button-1>", self.show_context_menu)

        self.tree.bind("<Control-a>", self.select_all)
        self.tree.bind("<Command-a>", self.select_all)

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
        genre_color_map = {}
        for genre in self.genre_tags:
            g_title = genre[1]
            g_color = genre[2]
            if g_title:
                if g_color is not None and str(g_color).strip():
                    self.tree.tag_configure(g_title, background=str(g_color).strip(), foreground="black")
                    genre_color_map[g_title] = str(g_color).strip()
                else:
                    genre_color_map[g_title] = None

        # clear old rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # insert new rows
        for index, book in enumerate(books):
            topics = db_get.get_book_topics_names(book[0])
            genre = book[7]
            genre_color = genre_color_map.get(genre)

            if genre and genre_color:
                tag = genre
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
            selected = self.tree.selection()
            if len(selected) > 1 and row_id in selected:
                self.delete_selected_books([int(i) for i in selected])
            else:
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
        self.app.close_book()

        # Reload table
        books = db_get.get_books()

        self.populate_table(books)

    def delete_selected_books(self, book_ids):
        count = len(book_ids)
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete {count} selected books?"
        )
        if not confirm:
            return

        db_update.delete_multiple_books(book_ids)
        self.app.close_book()
        books = db_get.get_books()
        self.populate_table(books)

    def on_book_selected(self, event):

        selected = self.tree.selection()

        if not selected:
            return

        if len(selected) == 1:
            book_id = int(selected[0])
            self.app.show_book_details(book_id)
        else:
            book_ids = [int(i) for i in selected]
            self.app.show_multi_book_details(book_ids)

    def select_all(self, event=None):
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children)
            book_ids = [int(i) for i in children]
            if len(book_ids) == 1:
                self.app.show_book_details(book_ids[0])
            else:
                self.app.show_multi_book_details(book_ids)
        return "break"

    def deselect_all(self, event=None):
        self.tree.selection_remove(self.tree.selection())
        self.app.close_book()
        return "break"

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        if len(selected) == 1:
            book_id = int(selected[0])
            self.app.show_book_details(book_id)
            self.app.details.edit_book(book_id)
        else:
            book_ids = [int(i) for i in selected]
            self.app.show_multi_book_details(book_ids)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        if len(selected) == 1:
            self.delete_book(int(selected[0]))
        else:
            self.delete_selected_books([int(i) for i in selected])

    def show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            current_selection = self.tree.selection()
            if row_id not in current_selection:
                self.tree.selection_set(row_id)
        selected = self.tree.selection()
        if selected:
            self.context_menu.tk_popup(event.x_root, event.y_root)