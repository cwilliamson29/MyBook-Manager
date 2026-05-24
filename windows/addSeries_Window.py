import tkinter as tk
from tkinter import messagebox
from db import database


class AddSeriesWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent.root)

        self.parent = parent

        self.title("Add Series")
        self.geometry("300x250")

        # Label first name
        tk.Label(self, text="Series Title:").pack(pady=10)

        # Entry field first name
        self.series_entry = tk.Entry(self, width=30)
        self.series_entry.pack(pady=5)

        # Load authors
        self.authors = database.get_authors()

        tk.Label(self, text="Select Author").pack(pady=5)

        self.selected_author = tk.StringVar()

        # map display name -> id
        self.author_map = {
            f"{first} {last}": author_id
            for author_id, first, last in self.authors
        }
        self.dropdown = tk.OptionMenu(
            self,
            self.selected_author,
            *self.author_map.keys()
        )
        self.dropdown.pack()

        # Button
        tk.Button(
            self,
            text="Add Author",
            command=self.save_series
        ).pack(pady=10)

        # Handle closing properly
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def save_series(self):
        seriesname = self.series_entry.get().strip()
        author_name = self.selected_author.get()
        author_id = self.author_map[author_name]


        if not seriesname:
            messagebox.showerror("Error", "Series title cannot be empty")
            return

        database.add_series(seriesname, author_id)

        messagebox.showinfo("Success", f"Series '{seriesname}' added!")

        self.on_close()

    def on_close(self):
        # Reset reference in main app
        self.parent.add_author_window = None
        self.destroy()