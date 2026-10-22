import sqlite3
from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox

from db.config import DB_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / DB_NAME if not Path(DB_NAME).is_absolute() else Path(DB_NAME)

def backup_database(parent=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_name = f"my_app_backup_{timestamp}.db"

    backup_path = filedialog.asksaveasfilename(
        parent=parent,
        title="Save Database Backup",
        defaultextension=".db",
        initialfile=default_name,
        filetypes=[("SQLite database", "*.db"), ("All files", "*.*")]
    )

    if not backup_path:
        return None  # User cancelled

    try:
        # This safely creates a consistent backup, including while the app is open.
        with sqlite3.connect(DB_PATH) as source_conn:
            with sqlite3.connect(backup_path) as backup_conn:
                source_conn.backup(backup_conn)

        messagebox.showinfo("Backup Complete", f"Successfully saved database backup to:\n{backup_path}", parent=parent)
        return backup_path

    except sqlite3.Error as error:
        messagebox.showerror("Backup Failed", str(error), parent=parent)
        return False

def quick_backup_database(parent=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_name = f"my_app_backup_{timestamp}.db"
    backup_path = PROJECT_ROOT / default_name

    try:
        with sqlite3.connect(DB_PATH) as source_conn:
            with sqlite3.connect(backup_path) as backup_conn:
                source_conn.backup(backup_conn)

        messagebox.showinfo("Quick Backup Complete", f"Snapshot saved to project folder:\n{default_name}", parent=parent)
        return str(backup_path)

    except sqlite3.Error as error:
        messagebox.showerror("Quick Backup Failed", str(error), parent=parent)
        return False