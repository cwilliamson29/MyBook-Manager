import sqlite3
from db import config

def get_connection():
    return sqlite3.connect(config.DB_NAME)

def get_from_db(sql, data):
    conn = get_connection()
    cur = conn.cursor()
    if data is None:
        cur.execute(sql)
    else:
        cur.execute(sql, data)
    rows = cur.fetchall()
    conn.close()

    return rows

def get_from_db_single(sql, data):
    conn = get_connection()
    cur = conn.cursor()
    if data is None:
        cur.execute(sql)
    else:
        cur.execute(sql, data)

    return [
        row[0] for row in cur.fetchall()
    ]
def get_authors():
    sql = "SELECT id, first_name, last_name FROM authors ORDER BY first_name, last_name"
    return get_from_db(sql, None)


def get_author_by_id(author_id):
    sql = "SELECT id, first_name, last_name FROM authors WHERE id = ?"
    return get_from_db(sql, (author_id,))


def get_all_series():
    sql = """
        SELECT
            series.id,
            series.title,
            authors.id,
            authors.first_name,
            authors.last_name
        FROM series
        LEFT JOIN authors
            ON series.author_id = authors.id
        ORDER BY
            series.title,
            authors.first_name,
            authors.last_name
    """
    return get_from_db(sql, None)


def get_series_by_id(series_id):
    sql = "SELECT id, title, author_id FROM series WHERE id = ?"
    return get_from_db(sql, (series_id,))


def get_author_stats(author_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM books WHERE author_id = ?", (author_id,))
        book_count = cur.fetchone()[0]
    except Exception:
        book_count = 0
    try:
        cur.execute("SELECT COUNT(*) FROM series WHERE author_id = ?", (author_id,))
        series_count = cur.fetchone()[0]
    except Exception:
        series_count = 0
    conn.close()
    return {"books": book_count, "series": series_count}


def get_series_stats(series_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM books WHERE series_id = ?", (series_id,))
        book_count = cur.fetchone()[0]
    except Exception:
        book_count = 0
    conn.close()
    return {"books": book_count}


def get_genres():
    sql = "SELECT id, title, color_scheme FROM genre ORDER BY title COLLATE NOCASE ASC"
    return get_from_db(sql, None)

def get_genres_titles():
    sql = "SELECT id, title FROM genre ORDER BY title COLLATE NOCASE ASC"
    return get_from_db(sql, None)

def get_genres_by_title(title):
    sql = "SELECT * FROM genre WHERE title = ?"
    return get_from_db(sql, (title,))

def get_genre_by_id(genre_id):
    sql = "SELECT id, title, color_scheme FROM genre WHERE id = ?"
    return get_from_db(sql, (genre_id,))

def get_genre_stats(genre_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM books WHERE genre_id = ?", (genre_id,))
        book_count = cur.fetchone()[0]
    except Exception:
        book_count = 0
    finally:
        conn.close()
    return {"books": book_count}

def get_genres_with_counts():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT genre.id, genre.title, genre.color_scheme, COUNT(books.id) as book_count
            FROM genre
            LEFT JOIN books ON genre.id = books.genre_id
            GROUP BY genre.id, genre.title, genre.color_scheme
            ORDER BY genre.title COLLATE NOCASE ASC
        """)
        return cur.fetchall()
    except Exception:
        return []
    finally:
        conn.close()

def get_series_by_author(author_id):
    sql = "SELECT id, title FROM series WHERE author_id = ?"
    return get_from_db(sql, (author_id,))

def get_topics():
    sql = "SELECT id, name FROM topics ORDER BY name"
    return get_from_db(sql, None)

def get_book_topics_names(book_id):
    conn = get_connection()
    cur = conn.cursor()
    sql = "SELECT topics.name FROM topics JOIN book_topics ON topics.id = book_topics.topic_id WHERE book_topics.book_id = ?"
    cur.execute(sql, (book_id,))
    return [
        row[0]
        for row in cur.fetchall()
    ]

def get_book_topics_id(book_id):
    conn = get_connection()
    cur = conn.cursor()
    sql = "SELECT topics.id FROM topics JOIN book_topics ON topics.id = book_topics.topic_id WHERE book_topics.book_id = ?"
    cur.execute(sql, (book_id,))
    return [
        row[0]
        for row in cur.fetchall()
    ]

def get_topic_names(topic_id):
    sql = "SELECT name FROM topics WHERE id = ?"
    return get_from_db(sql, (topic_id,))

def get_books():
    sql = """
        SELECT
            books.id,
            books.title,
            series.title,
            books.num_in_series,
            authors.first_name,
            authors.last_name,
            books.rating,
            genre.title,
            books.isbn,
            books.nls_order
        FROM books

        LEFT JOIN series 
            ON books.series_id = series.id

        LEFT JOIN authors
            ON books.author_id = authors.id
        
        LEFT JOIN genre
            ON books.genre_id = genre.id

        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series
    """

    return get_from_db(sql, None)

def get_books_by_author(author_id):
    sql = """
        SELECT
            books.id,
            books.title,
            series.title,
            books.num_in_series,
            authors.first_name,
            authors.last_name,
            books.rating,
            genre.title,
            books.isbn,
            books.nls_order
        FROM books
        LEFT JOIN series
            ON books.series_id = series.id
        LEFT JOIN authors
            ON books.author_id = authors.id
        LEFT JOIN genre
            ON books.genre_id = genre.id
        WHERE authors.id = ?
        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series
    """
    return get_from_db(sql, (author_id,))

def get_books_by_topic(topic_id):
    sql = """
        SELECT
            books.id,
            books.title,
            series.title,
            books.num_in_series,
            authors.first_name,
            authors.last_name,
            books.rating,
            genre.title,
            books.isbn,
            books.nls_order
        FROM books
        LEFT JOIN series
            ON books.series_id = series.id
        LEFT JOIN authors
            ON books.author_id = authors.id
        LEFT JOIN genre
            ON books.genre_id = genre.id
        JOIN book_topics
            ON books.id = book_topics.book_id
        WHERE book_topics.topic_id = ?
        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series
    """
    return get_from_db(sql, (topic_id,))

def get_books_by_genre(genre_id):
    sql = """
        SELECT
            books.id,
            books.title,
            series.title,
            books.num_in_series,
            authors.first_name,
            authors.last_name,
            books.rating,
            genre.title,
            books.isbn,
            books.nls_order
        FROM books
        LEFT JOIN series
            ON books.series_id = series.id
        LEFT JOIN authors
            ON books.author_id = authors.id
        LEFT JOIN genre
            ON books.genre_id = genre.id
        
        WHERE books.genre_id = ?
        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series
    """
    return get_from_db(sql, (genre_id,))

def get_books_by_topic_and_genre(topic_id, genre_id):
    sql = """
        SELECT
            books.id,
            books.title,
            series.title,
            books.num_in_series,
            authors.first_name,
            authors.last_name,
            books.rating,
            genre.title,
            books.isbn,
            books.nls_order
        FROM books
        LEFT JOIN series
            ON books.series_id = series.id
        LEFT JOIN authors
            ON books.author_id = authors.id
        LEFT JOIN genre
            ON books.genre_id = genre.id
        JOIN book_topics
            ON books.id = book_topics.book_id
        WHERE 
            book_topics.topic_id = ?
            AND books.genre_id = ?
        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series
    """
    return get_from_db(sql, (topic_id,genre_id,))

def get_book_by_id(book_id):
    sql = ("""SELECT
            books.id,
            books.title,
            series.id,
            series.title,
            books.num_in_series,
            authors.id,
            authors.first_name,
            authors.last_name,
            books.rating,
            genre.title,
            books.isbn,
            books.nls_order,
            description,
            cover_image
        FROM books
        LEFT JOIN series
            ON books.series_id = series.id
        LEFT JOIN authors
            ON books.author_id = authors.id
        LEFT JOIN genre
            ON books.genre_id = genre.id
        WHERE books.id = ?
        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series""")
    row = get_from_db(sql, (book_id,))
    return row

def get_book_cover(book_id):
    """
    Returns the cover image bytes for a book, or None.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT cover_image FROM books WHERE id = ?", (book_id,))
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
        return None
    except Exception as e:
        print("Error getting book cover:", e)
        return None
    finally:
        conn.close()

def get_books_missing_covers_count():
    """
    Returns the count of books with an ISBN that currently have no cover image.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM books 
            WHERE isbn IS NOT NULL 
              AND TRIM(isbn) != '' 
              AND (cover_image IS NULL OR LENGTH(cover_image) = 0)
        """)
        return cur.fetchone()[0]
    except Exception as e:
        print("Error getting books missing covers count:", e)
        return 0
    finally:
        conn.close()

def get_books_missing_covers():
    """
    Returns a list of (id, title, isbn) for books with an ISBN but no cover image.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, title, isbn FROM books 
            WHERE isbn IS NOT NULL 
              AND TRIM(isbn) != '' 
              AND (cover_image IS NULL OR LENGTH(cover_image) = 0)
            ORDER BY id
        """)
        return cur.fetchall()
    except Exception as e:
        print("Error getting books missing covers:", e)
        return []
    finally:
        conn.close()

def get_database_stats():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM books")
        books_count = cur.fetchone()[0]
    except Exception:
        books_count = 0

    try:
        cur.execute("SELECT COUNT(*) FROM authors")
        authors_count = cur.fetchone()[0]
    except Exception:
        authors_count = 0

    try:
        cur.execute("SELECT COUNT(*) FROM series")
        series_count = cur.fetchone()[0]
    except Exception:
        series_count = 0

    try:
        cur.execute("SELECT COUNT(*) FROM genre")
        genre_count = cur.fetchone()[0]
    except Exception:
        genre_count = 0

    try:
        cur.execute("SELECT COUNT(*) FROM topics")
        topics_count = cur.fetchone()[0]
    except Exception:
        topics_count = 0

    conn.close()

    return {
        "books": books_count,
        "authors": authors_count,
        "series": series_count,
        "genres": genre_count,
        "topics": topics_count
    }
