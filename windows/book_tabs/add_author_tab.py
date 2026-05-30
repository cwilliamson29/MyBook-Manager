import tkinter as tk

from db import db_add


class AuthorTab(tk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        tk.Label(self, text="First Name").grid(row=0, column=0, sticky="e")
        self.first = tk.Entry(self, width=20)
        self.first.grid(row=0, column=1, sticky="w")

        tk.Label(self, text="Last Name").grid(row=1, column=0, sticky="e")
        self.last = tk.Entry(self, width=20)
        self.last.grid(row=1, column=1, sticky="w")

        self.error_label = tk.Label(self, text="", fg="red")
        self.success_label = tk.Label(self, text="Author Successfully Added!", fg="green")

        tk.Button(
            self,
            text="Add Author",
            command=self.add_author
        ).grid(row=3, column=1)

    def add_author(self):
        self.error_label.grid_forget()
        self.success_label.grid_forget()

        fname = self.first.get().strip()
        lname = self.last.get().strip()

        if not fname or not lname:
            if not fname:
                self.first.config(bg="#FF9999", fg="black")

            if not lname:
                self.last.config(bg="#FF9999", fg="black")

            self.error_label.config(text="First and last name required")
            self.error_label.grid(row=2, column=1)
            return
        data = (fname, lname)
        db_attempt = db_add.add_author(data)

        if db_attempt == "success":
            self.first.delete(0, tk.END)
            self.last.delete(0, tk.END)
            self.first.config(bg='SystemButtonFace')
            self.last.config(bg='SystemButtonFace')

            self.success_label.grid(row=2, column=1)
        else:
            self.error_label.config(text=f"Error: {db_attempt}!", fg="red")
            self.error_label.grid(row=2, column=1)