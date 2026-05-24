import tkinter as tk
from tkinter import messagebox
import database


class EditBookWindow(tk.Toplevel):

    def __init__(self, parent, book_id):
        super().__init__(parent)

        self.parent = parent
        self.book_id = book_id

        self.title("Edit Book")
        self.geometry("400x165")

        # Get book data
        book = database.get_book_by_id(book_id)

        # Title
        tk.Label(self, text="Title:").grid(row=0, column=0, sticky="e",pady=5)

        self.title_entry = tk.Entry(self, width=30)
        self.title_entry.grid(row=0, column=1, sticky="w", pady=5)

        self.title_entry.insert(0, book[1])

        # Published date
        tk.Label(self, text="Published Date:").grid(row=1, column=0, sticky="e",pady=5)

        self.date_entry = tk.Entry(self, width=10)
        self.date_entry.grid(row=1, column=1, sticky="w",pady=5)

        self.date_entry.insert(0, book[6])

        # NLS Order
        tk.Label(self, text="NLS Order:").grid(row=2, column=0, sticky="e",pady=5)

        self.nls_entry = tk.Entry(self, width=20)
        self.nls_entry.grid(row=2, column=1, sticky="w",pady=5)

        self.nls_entry.insert(0, book[5])

        # print(book)

        # Save button
        tk.Button(
            self,
            text="Save Changes",
            command=self.save_changes
        ).grid(row=3, column=1, pady=5)

    def save_changes(self):

        title = self.title_entry.get().strip()
        pub_date = self.date_entry.get().strip()
        nls_order = self.nls_entry.get().strip()

        if not title:
            messagebox.showerror(
                "Error",
                "Title cannot be empty"
            )
            return

        database.update_book(
            self.book_id,
            title,
            pub_date,
            nls_order
        )

        # Refresh main table
        self.parent.load_books()

        self.destroy()