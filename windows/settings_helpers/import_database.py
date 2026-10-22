import os
import shutil
from pathlib import Path
from tkinter import filedialog, messagebox
from db.config import DB_NAME

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / DB_NAME if not Path(DB_NAME).is_absolute() else Path(DB_NAME)

def import_database(app=None, parent=None):
    selected_path = filedialog.askopenfilename(
        parent=parent,
        title="Choose a Database Backup to Restore",
        filetypes=[("SQLite database", "*.db"), ("All files", "*.*")]
    )

    if not selected_path:
        return None

    confirmed = messagebox.askyesno(
        "Confirm Database Restore",
        "This will replace your current active database with the selected backup file.\n\n"
        "A safety snapshot of your current database will be created automatically before restoring.\n\n"
        "Do you want to proceed?",
        parent=parent
    )
    if not confirmed:
        return False

    try:
        # Save a recovery copy of the current DB before overwriting it.
        recovery_path = DB_PATH.with_name(f"{DB_PATH.stem}_before_import.db")
        if DB_PATH.exists():
            shutil.copy2(DB_PATH, recovery_path)

        # Copy the selected database to the active DB path
        shutil.copy2(selected_path, DB_PATH)

        if app is not None:
            if hasattr(app, "load_books"):
                app.load_books()
            if hasattr(app, "load_authors_into_filter"):
                app.load_authors_into_filter()
            if hasattr(app, "load_genres_into_filter"):
                app.load_genres_into_filter()
            if hasattr(app, "load_topics_into_filter"):
                app.load_topics_into_filter()

        messagebox.showinfo(
            "Restore Complete",
            "Database restored successfully!\nThe application view has been refreshed with the restored data.",
            parent=parent
        )
        return True

    except OSError as error:
        messagebox.showerror("Restore Failed", str(error), parent=parent)
        return False