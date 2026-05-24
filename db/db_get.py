import sqlite3
from db.config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)


def get_authors():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, first_name, last_name FROM authors ORDER BY first_name")
    rows = cur.fetchall()

    conn.close()
    return rows


def get_series_by_author(author_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title
        FROM series
        WHERE author_id = ?
    """, (author_id,))

    rows = cur.fetchall()

    conn.close()

    return rows


def get_books():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            books.id,
            books.title,
            series.title,
            books.num_in_series,
            authors.first_name,
            authors.last_name,
            books.published_date,
            books.nls_order
        FROM books

        LEFT JOIN series 
            ON books.series_id = series.id

        LEFT JOIN authors
            ON books.author_id = authors.id

        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


def get_books_by_author(author_id):
    # print(author_id)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            books.id,
            books.title,
            series.title,
            books.num_in_series,
            authors.first_name,
            authors.last_name,
            books.published_date,
            books.nls_order
        FROM books
        LEFT JOIN series
            ON books.series_id = series.id
        LEFT JOIN authors
            ON books.author_id = authors.id
        WHERE authors.id = ?
        ORDER BY
            authors.first_name,
            authors.last_name,
            series.title,
            books.num_in_series
    """, (author_id,))

    rows = cur.fetchall()
    conn.close()

    return rows


def get_book_by_id(book_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM books
        WHERE id = ?
    """, (book_id,))

    row = cur.fetchone()

    conn.close()

    return row