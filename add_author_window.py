import tkinter as tk
from tkinter import messagebox
import database


class AddAuthorWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent.root)

        self.parent = parent

        self.title("Add Author")
        self.geometry("300x250")

        # Label first name
        tk.Label(self, text="Author First Name:").pack(pady=10)

        # Entry field first name
        self.fname_entry = tk.Entry(self, width=30)
        self.fname_entry.pack(pady=5)

        # Label last name
        tk.Label(self, text="Author Last Name:").pack(pady=10)

        # Entry field
        self.lname_entry = tk.Entry(self, width=30)
        self.lname_entry.pack(pady=5)

        # Button
        tk.Button(
            self,
            text="Add Author",
            command=self.save_author
        ).pack(pady=10)

        # Handle closing properly
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def save_author(self):

        fname = self.fname_entry.get().strip()
        lname = self.lname_entry.get().strip()

        if not fname or not lname:
            messagebox.showerror("Error", "Author name cannot be empty")
            return

        database.add_author(fname, lname)

        messagebox.showinfo("Success", f"Author '{fname + " " + lname}' added!")

        self.parent.load_authors_into_filter()

        self.on_close()

    def on_close(self):
        # Reset reference in main app
        self.parent.add_author_window = None
        self.destroy()