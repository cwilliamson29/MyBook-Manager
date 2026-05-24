import sqlite3
from db.config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

def update_book(book_id, title,pub_date,nls_order):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE books
        SET
            title = ?,
            published_date = ?,
            nls_order = ?
        WHERE id = ?
    """, (title, pub_date, nls_order, book_id,))

    conn.commit()
    conn.close()

def delete_book(book_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM books WHERE id = ?", (book_id,))

    conn.commit()
    conn.close()