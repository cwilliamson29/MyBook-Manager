import sqlite3
from db.config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

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

def update_book(data):
    sql ="""
        UPDATE books
        SET
            title = ?,
            author_id = ?,
            series_id = ?,
            num_in_series = ?,
            rating = ?,
            genre_id = ?,
            isbn = ?,
            nls_order = ?,
            description = ?
        WHERE id = ?
    """
    db = add_to_db(sql, data)
    return db

def remove_book_topic(data):
    rem = """DELETE FROM book_topics WHERE book_id = ?"""
    db = add_to_db(rem, data)
    return db

def delete_book(book_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM books WHERE id = ?", (book_id,))

    conn.commit()
    conn.close()