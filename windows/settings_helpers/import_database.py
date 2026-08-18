import os
import shutil
from pathlib import Path
from tkinter import filedialog, messagebox
from db.config import DB_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "books.db"

def import_database():
    selected_path = filedialog.askopenfilename(
        title="Choose a database backup to import",
        filetypes=[("SQLite database", "*.db"), ("All files", "*.*")]
    )

    if not selected_path:
        return

    confirmed = messagebox.askyesno(
        "Import database?",
        "This will replace your current database.\n\n"
        "Your existing database will be backed up automatically first."
    )
    if not confirmed:
        return

    try:
        # Save a recovery copy of the current DB before overwriting it.
        recovery_path = DB_PATH.with_name(f"{DB_PATH.stem}_before_import.db")
        shutil.copy2(DB_PATH, recovery_path)

        # Close any active connections to DB_PATH before this step.
        shutil.copy2(selected_path, DB_PATH)

        messagebox.showinfo(
            "Import complete",
            "Database imported successfully.\nRestart the app to load the new data."
        )

    except OSError as error:
        messagebox.showerror("Import failed", str(error))