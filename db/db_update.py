import sqlite3
from db import config

def get_connection():
    return sqlite3.connect(config.DB_NAME)

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

def update_book_cover(book_id, image_data):
    """
    Updates or removes the cover image for a book.
    image_data: bytes or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE books SET cover_image = ? WHERE id = ?", (image_data, book_id))
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error in update_book_cover: ", e)
        conn.rollback()
        return str(e)
    finally:
        conn.close()

def update_book_isbn(book_id, isbn):
    """
    Updates the ISBN for a book.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE books SET isbn = ? WHERE id = ?", (isbn, book_id))
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error in update_book_isbn: ", e)
        conn.rollback()
        return str(e)
    finally:
        conn.close()

def update_genre_color(genre_id, color_scheme):
    """
    Updates the color scheme for a genre.
    color_scheme: hex color string (e.g. '#FF5733') or None / empty string
    """
    clean_color = str(color_scheme).strip() if color_scheme else None
    if clean_color == "":
        clean_color = None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE genre SET color_scheme = ? WHERE id = ?", (clean_color, genre_id))
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error in update_genre_color: ", e)
        conn.rollback()
        return str(e)
    finally:
        conn.close()

def update_genre(genre_id, title, color_scheme):
    """
    Updates the title and color scheme for a genre.
    """
    title = str(title).strip()
    if not title:
        return "Genre title cannot be empty"

    clean_color = str(color_scheme).strip() if color_scheme else None
    if clean_color == "":
        clean_color = None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE genre SET title = ?, color_scheme = ? WHERE id = ?", (title, clean_color, genre_id))
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error in update_genre: ", e)
        conn.rollback()
        return str(e)
    finally:
        conn.close()

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


from db.database import clean_author_parts, normalize_author_key, combine_duplicate_authors

def update_author(author_id, first_name, last_name):
    first_name, last_name = clean_author_parts(first_name, last_name)
    key = normalize_author_key(first_name, last_name)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if another author exists with the same normalized key
        cursor.execute("SELECT id, first_name, last_name FROM authors WHERE id != ?", (author_id,))
        other_authors = cursor.fetchall()
        matching_other = None
        for oid, ofirst, olast in other_authors:
            if normalize_author_key(ofirst, olast) == key:
                matching_other = oid
                break

        if matching_other is not None:
            # Merge other author into author_id
            cursor.execute("UPDATE books SET author_id = ? WHERE author_id = ?", (author_id, matching_other))

            cursor.execute("SELECT id, title FROM series WHERE author_id = ?", (matching_other,))
            dup_series = cursor.fetchall()
            for s_id, s_title in dup_series:
                cursor.execute(
                    "SELECT id FROM series WHERE author_id = ? AND LOWER(TRIM(title)) = LOWER(TRIM(?))",
                    (author_id, s_title)
                )
                existing_s = cursor.fetchone()
                if existing_s:
                    canonical_s_id = existing_s[0]
                    cursor.execute("UPDATE books SET series_id = ? WHERE series_id = ?", (canonical_s_id, s_id))
                    cursor.execute("DELETE FROM series WHERE id = ?", (s_id,))
                else:
                    cursor.execute("UPDATE series SET author_id = ? WHERE id = ?", (author_id, s_id))

            cursor.execute("DELETE FROM authors WHERE id = ?", (matching_other,))

        cursor.execute("UPDATE authors SET first_name = ?, last_name = ? WHERE id = ?", (first_name, last_name, author_id))
        conn.commit()
        return "success"
    except sqlite3.Error as e:
        print("SQLite error in update_author: ", e)
        conn.rollback()
        return str(e)
    finally:
        conn.close()


def update_series(series_id, title, author_id=None):
    if author_id is not None:
        sql = "UPDATE series SET title = ?, author_id = ? WHERE id = ?"
        return add_to_db(sql, (title, author_id, series_id))
    else:
        sql = "UPDATE series SET title = ? WHERE id = ?"
        return add_to_db(sql, (title, series_id))