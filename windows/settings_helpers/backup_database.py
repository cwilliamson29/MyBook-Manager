import sqlite3
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk

from db.config import DB_NAME

DB_PATH = Path(DB_NAME)

def backup_database():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_name = f"my_app_backup_{timestamp}.db"

    backup_path = filedialog.asksaveasfilename(
        title="Save database backup",
        defaultextension=".db",
        initialfile=default_name,
        filetypes=[("SQLite database", "*.db"), ("All files", "*.*")]
    )

    if not backup_path:
        return  # User cancelled

    try:
        # This safely creates a consistent backup, including while the app is open.
        with sqlite3.connect(DB_PATH) as source_conn:
            with sqlite3.connect(backup_path) as backup_conn:
                source_conn.backup(backup_conn)

        messagebox.showinfo("Backup complete", f"Saved backup to:\n{backup_path}")

    except sqlite3.Error as error:
        messagebox.showerror("Backup failed", str(error))