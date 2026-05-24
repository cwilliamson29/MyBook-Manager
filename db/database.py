import sqlite3

DB_NAME = "books.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Create Books
    cursor.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        series_id INTEGER,
        num_in_series INTEGER,
        book_read BOOLEAN NOT NULL DEFAULT FALSE,
        nls_order TEXT,
        published_date TEXT,
        rating INTEGER,
        genre_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        FOREIGN KEY(author_id) REFERENCES authors(id),
        FOREIGN KEY(series_id) REFERENCES series(id)
        FOREIGN KEY(genre_id) REFERENCES genre(id)
        )''')
    conn.commit()

    # Create Authors
    cursor.execute('''CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
            )''')
    conn.commit()

    # Create Series
    cursor.execute('''CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            FOREIGN KEY(author_id) REFERENCES authors(id))''')
    conn.commit()

    # Create Genre
    cursor.execute("""CREATE TABLE IF NOT EXISTS genre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
            )""")
    conn.commit()

    conn.close()

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
    cursor.execute("INSERT INTO genre (title) VALUES (?)",(title))

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
def update_book(book_id, title,pub_date,nls_order):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE books
        SET
            title = ?,
            published_date = ?,
            nls_order = ?
        WHERE id = ?
    """, (title, pub_date, nls_order, book_id,))

    conn.commit()
    conn.close()

def delete_book(book_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM books WHERE id = ?", (book_id,))

    conn.commit()
    conn.close()