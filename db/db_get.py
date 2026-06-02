import sqlite3
from db.config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_from_db(sql, data):
    conn = get_connection()
    cur = conn.cursor()
    if data is None:
        cur.execute(sql)
    else:
        cur.execute(sql, (data))
    rows = cur.fetchall()
    conn.close()

    return rows

def get_authors():
    sql = "SELECT id, first_name, last_name FROM authors ORDER BY first_name"
    return get_from_db(sql, None)


def get_genres():
    sql = "SELECT id, title, color_scheme FROM genre ORDER BY title"
    return get_from_db(sql, None)
def get_genres_titles():
    sql = "SELECT id, title FROM genre ORDER BY title"
    return get_from_db(sql, None)
def get_genres_by_title(title):
    sql = "SELECT * FROM genre WHERE title = ?"
    return get_from_db(sql, (title,))

def get_series_by_author(author_id):
    sql = "SELECT id, title FROM series WHERE author_id = ?"
    return get_from_db(sql, (author_id,))


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

def get_book_by_id(book_id):
    sql = "SELECT * FROM books WHERE id = ?"
    row = get_from_db(sql, (book_id,))
    # print("**********************")
    # print(row)
    # print("**********************")
    return row
