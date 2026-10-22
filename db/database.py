import re
import sqlite3

from db.config import DB_NAME

def get_connection(db_name=None):
    return sqlite3.connect(db_name if db_name is not None else DB_NAME)

def clean_author_token(token):
    if not token:
        return ""
    token = str(token).strip().strip("'\"`")
    parts = token.split()
    cleaned_words = []
    for w in parts:
        w_clean = w.strip("'\"`,;:")
        if len(w_clean) > 2 and w_clean.endswith("."):
            w_clean = w_clean.rstrip(".")
        cleaned_words.append(w_clean)
    return " ".join(cleaned_words).strip()

def clean_author_parts(first_name, last_name):
    first = clean_author_token(first_name)
    last = clean_author_token(last_name)
    return first, last

def normalize_author_key(first_name, last_name):
    first, last = clean_author_parts(first_name, last_name)
    full = f"{first} {last}".strip().lower()
    clean = re.sub(r'[^\w\s]', '', full)
    return " ".join(clean.split())

def combine_duplicate_authors(db_name=None):
    """
    Finds authors with spelling/punctuation variations (e.g. 'allison' vs 'allison.')
    and combines all books and series under a single author record.
    """
    conn = get_connection(db_name)
    cursor = conn.cursor()
    merged_count = 0
    reassigned_books = 0
    reassigned_series = 0

    try:
        cursor.execute("SELECT id, first_name, last_name FROM authors ORDER BY id ASC")
        all_authors = cursor.fetchall()

        groups = {}
        for aid, first, last in all_authors:
            key = normalize_author_key(first, last)
            if not key:
                continue
            groups.setdefault(key, []).append((aid, first, last))

        for key, authors_list in groups.items():
            if len(authors_list) <= 1:
                aid, first, last = authors_list[0]
                c_first, c_last = clean_author_parts(first, last)
                if (c_first, c_last) != (first, last):
                    cursor.execute(
                        "UPDATE authors SET first_name = ?, last_name = ? WHERE id = ?",
                        (c_first, c_last, aid)
                    )
                continue

            def author_quality_score(item):
                aid, f, l = item
                f_str = str(f or "").strip()
                l_str = str(l or "").strip()
                full = f"{f_str} {l_str}".strip()
                has_trailing_dot = f_str.endswith(".") or l_str.endswith(".")
                is_capitalized = full[0].isupper() if full else False
                return (
                    0 if has_trailing_dot else 10,
                    5 if is_capitalized else 0,
                    len(full),
                    -aid
                )

            sorted_authors = sorted(authors_list, key=author_quality_score, reverse=True)
            canonical_id, c_first_raw, c_last_raw = sorted_authors[0]
            canonical_first, canonical_last = clean_author_parts(c_first_raw, c_last_raw)

            cursor.execute(
                "UPDATE authors SET first_name = ?, last_name = ? WHERE id = ?",
                (canonical_first, canonical_last, canonical_id)
            )

            duplicate_ids = [aid for aid, _, _ in sorted_authors[1:]]

            for dup_id in duplicate_ids:
                cursor.execute(
                    "UPDATE books SET author_id = ? WHERE author_id = ?",
                    (canonical_id, dup_id)
                )
                reassigned_books += cursor.rowcount

                cursor.execute("SELECT id, title FROM series WHERE author_id = ?", (dup_id,))
                dup_series = cursor.fetchall()
                for s_id, s_title in dup_series:
                    cursor.execute(
                        "SELECT id FROM series WHERE author_id = ? AND LOWER(TRIM(title)) = LOWER(TRIM(?))",
                        (canonical_id, s_title)
                    )
                    existing_s = cursor.fetchone()
                    if existing_s:
                        canonical_s_id = existing_s[0]
                        cursor.execute("UPDATE books SET series_id = ? WHERE series_id = ?", (canonical_s_id, s_id))
                        cursor.execute("DELETE FROM series WHERE id = ?", (s_id,))
                    else:
                        cursor.execute("UPDATE series SET author_id = ? WHERE id = ?", (canonical_id, s_id))
                        reassigned_series += 1

                cursor.execute("DELETE FROM authors WHERE id = ?", (dup_id,))
                merged_count += 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error combining duplicate authors:", e)
        raise e
    finally:
        conn.close()

    return {
        "merged_authors": merged_count,
        "reassigned_books": reassigned_books,
        "reassigned_series": reassigned_series
    }

def create_tables(db_name=None):
    conn = get_connection(db_name)
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
        cover_image BLOB,
        audio_folder TEXT,
        audio_track TEXT,
        audio_position REAL DEFAULT 0.0,
        audio_speed REAL DEFAULT 1.0,
        FOREIGN KEY(author_id) REFERENCES authors(id),
        FOREIGN KEY(series_id) REFERENCES series(id),
        FOREIGN KEY(genre_id) REFERENCES genre(id)
        )''')
    conn.commit()

    # Ensure cover_image, audio_folder, audio_track, audio_position, and audio_speed columns exist for existing databases
    cursor.execute("PRAGMA table_info(books)")
    existing_book_cols = [col[1] for col in cursor.fetchall()]
    if "cover_image" not in existing_book_cols:
        cursor.execute("ALTER TABLE books ADD COLUMN cover_image BLOB")
        conn.commit()
    if "audio_folder" not in existing_book_cols:
        cursor.execute("ALTER TABLE books ADD COLUMN audio_folder TEXT")
        conn.commit()
    if "audio_track" not in existing_book_cols:
        cursor.execute("ALTER TABLE books ADD COLUMN audio_track TEXT")
        conn.commit()
    if "audio_position" not in existing_book_cols:
        cursor.execute("ALTER TABLE books ADD COLUMN audio_position REAL DEFAULT 0.0")
        conn.commit()
    if "audio_speed" not in existing_book_cols:
        cursor.execute("ALTER TABLE books ADD COLUMN audio_speed REAL DEFAULT 1.0")
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
    conn.commit()
    conn.close()

    combine_duplicate_authors(db_name)