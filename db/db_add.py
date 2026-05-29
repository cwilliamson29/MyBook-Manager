import sqlite3
from db.config import DB_NAME


def get_connection():
    return sqlite3.connect(DB_NAME)

def add_book(title, author_id, series_id, book_num, pub_date, nls_order):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author_id, series_id, num_in_series, published_date, nls_order) VALUES (?, ?, ?, ?,?,?)",(title, author_id, series_id, book_num, pub_date, nls_order))
    conn.commit()
    conn.close()

def add_series(title, author_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO series (title, author_id) VALUES (?, ?)",(title, author_id))
    conn.commit()
    conn.close()

def add_genre(title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO genre (title) VALUES (?)", (title,))
    conn.commit()
    print("entered into db")

def add_author(first_name, last_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO authors (first_name, last_name) VALUES (?, ?)", (first_name, last_name))
        conn.commit()
    except sqlite3.Error as e:
        print("SQLite error: ", e)
        return None
    finally:
        conn.close()