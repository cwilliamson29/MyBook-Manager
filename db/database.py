import sqlite3

from db.config import DB_NAME

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
        isbn TEXT,
        genre_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        description TEXT,
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
            title TEXT NOT NULL,
            color_scheme TEXT
            )""")
    conn.commit()

    # Create topics
    cursor.execute("""CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
            )""")
    conn.commit()

    # Book topics
    cursor.execute("""CREATE TABLE IF NOT EXISTS book_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            FOREIGN KEY(book_id) REFERENCES books(id),
            FOREIGN KEY(topic_id) REFERENCES topics(id)
            )""")

    conn.close()