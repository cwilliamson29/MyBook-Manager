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

    cur.execute("DELETE FROM book_topics WHERE book_id = ?", (book_id,))
    cur.execute("DELETE FROM books WHERE id = ?", (book_id,))

    conn.commit()
    conn.close()

def bulk_update_genre_and_topics(book_ids, genre_id=None, update_genre=False, topic_ids=None, update_topics=False):
    if not book_ids:
        return "success"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        if update_genre:
            placeholders = ",".join("?" for _ in book_ids)
            cursor.execute(f"UPDATE books SET genre_id = ? WHERE id IN ({placeholders})", [genre_id] + list(book_ids))

        if update_topics:
            placeholders = ",".join("?" for _ in book_ids)
            cursor.execute(f"DELETE FROM book_topics WHERE book_id IN ({placeholders})", list(book_ids))
            if topic_ids:
                pairs = [(book_id, topic_id) for book_id in book_ids for topic_id in topic_ids]
                cursor.executemany("INSERT INTO book_topics (book_id, topic_id) VALUES (?, ?)", pairs)

        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error in bulk_update_genre_and_topics: ", e)
        conn.rollback()
        return str(e)
    finally:
        conn.close()

def delete_multiple_books(book_ids):
    if not book_ids:
        return "success"
    conn = get_connection()
    cur = conn.cursor()
    try:
        placeholders = ",".join("?" for _ in book_ids)
        cur.execute(f"DELETE FROM book_topics WHERE book_id IN ({placeholders})", list(book_ids))
        cur.execute(f"DELETE FROM books WHERE id IN ({placeholders})", list(book_ids))
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error in delete_multiple_books: ", e)
        conn.rollback()
        return str(e)
    finally:
        conn.close()