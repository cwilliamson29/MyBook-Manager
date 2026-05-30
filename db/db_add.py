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
    #conn = get_connection()
    #cursor = conn.cursor()
    #cursor.execute("INSERT INTO genre (title) VALUES (?)", (title,))
    #conn.commit()
    sql = "INSERT INTO genre (title) VALUES (?)"
    db = add_to_db(sql, title)
    return db

def add_author(data):
    sql = "INSERT INTO authors (first_name, last_name) VALUES (?, ?)"
    db = add_to_db(sql, data)
    return db

def add_to_db(sql, args):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, args)
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error: ", e)
        return e
    finally:
        conn.close()
