import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import sqlite3
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox

from db.config import DB_NAME
from windows.settings_helpers.backup_database import backup_database
from windows.settings_helpers.import_database import import_database


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app.root)

        self.withdraw()

        self.app = app

        self.title("Settings")

        self.center_on_parent(app.root, 500, 680)


        self.deiconify()

        backup = ctk.CTkButton(self, text="Backup DB", command=backup_database, height=30, width=30, corner_radius=5, border_color="blue", font=("Arial", 30))
        imp = ctk.CTkButton(self, text="Import DB", command=import_database, height=30, width=30, corner_radius=5, border_color="blue", font=("Arial", 30))
        backup.grid(column=0, row=0)
        imp.grid(column=0, row=1)

    def center_on_parent(self, parent, width, height):
        parent.update_idletasks()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()

        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

