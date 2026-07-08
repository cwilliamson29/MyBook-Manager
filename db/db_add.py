import sqlite3
from db.config import DB_NAME


def get_connection():
    return sqlite3.connect(DB_NAME)

def add_book(data):
    sql = "INSERT INTO books (title, author_id, series_id, num_in_series, rating, genre_id, isbn, nls_order, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    db = add_to_db(sql, data)
    return db

def add_series(data):
    sql = "INSERT INTO series (title, author_id) VALUES (?, ?)"
    db = add_to_db(sql, data)
    return db

def add_genre(data):
    sql = "INSERT INTO genre (title, color_scheme) VALUES (?, ?)"
    db = add_to_db(sql, data)
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
