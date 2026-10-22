import sqlite3
from db import config
from db.database import clean_author_parts, normalize_author_key


def get_connection():
    return sqlite3.connect(config.DB_NAME)

def add_book(data):
    if len(data) == 10:
        sql = "INSERT INTO books (title, author_id, series_id, num_in_series, rating, genre_id, isbn, nls_order, description, cover_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    else:
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
    first_name, last_name = data
    first_name, last_name = clean_author_parts(first_name, last_name)
    key = normalize_author_key(first_name, last_name)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, first_name, last_name FROM authors")
        authors = cursor.fetchall()
        for aid, f, l in authors:
            if normalize_author_key(f, l) == key:
                return "success", aid

        cursor.execute("INSERT INTO authors (first_name, last_name) VALUES (?, ?)", (first_name, last_name))
        aid = cursor.lastrowid
        conn.commit()
        return "success", aid
    except sqlite3.Error as e:
        print("SQLite error in add_author: ", e)
        return e, None
    finally:
        conn.close()

def add_topic(data):
    sql = "INSERT INTO topics (name) VALUES (?)"
    db = add_to_db(sql, data)
    return db

def add_book_topics(data):
    sql = "INSERT INTO book_topics (book_id, topic_id) VALUES (?, ?)"
    db = add_to_db(sql, data)
    return db

def add_to_db(sql, args):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, args)
        id = cursor.lastrowid
        conn.commit()
        return "success", id
    except sqlite3.Error as e:
        print("SQLite error: ", e)
        return e
    finally:
        conn.close()
