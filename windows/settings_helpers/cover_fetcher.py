import io
import re
import hashlib
import requests
from PIL import Image

from db import db_get, db_update


def clean_isbn(isbn_input) -> str:
    """
    Cleans and extracts a valid ISBN string (ISBN-10 or ISBN-13).
    Removes hyphens, spaces, and extraneous punctuation.
    """
    if isbn_input is None:
        return ""
    
    raw = str(isbn_input).strip()
    if not raw:
        return ""
    
    # Strip common prefixes like 'ISBN:', 'ISBN-13:', etc.
    raw = re.sub(r'(?i)^isbn(?:-1[03])?[:\s]*', '', raw)
    
    # Extract valid ISBN characters (digits and 'X')
    chars = [c for c in raw if c.isdigit() or c.upper() == 'X']
    clean = "".join(chars).upper()
    
    # If there's extra text embedded, try finding 10 or 13 char sequences
    if len(clean) not in (10, 13):
        # Look for a 13-digit sequence starting with 978 or 979
        match13 = re.search(r'97[89]\d{10}', clean)
        if match13:
            return match13.group(0)
        # Look for a 10-char sequence
        match10 = re.search(r'\d{9}[\dX]', clean)
        if match10:
            return match10.group(0)
            
    return clean


def optimize_image_bytes(raw_bytes: bytes, max_dimension: int = 1200) -> bytes:
    """
    Validates and optimizes image bytes for database storage.
    Downscales if exceeding max_dimension, and saves as standard JPEG or PNG.
    """
    with Image.open(io.BytesIO(raw_bytes)) as pil_img:
        img_copy = pil_img.copy()

    if img_copy.width > max_dimension or img_copy.height > max_dimension:
        img_copy.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    out_io = io.BytesIO()
    if img_copy.mode in ("RGBA", "LA", "P"):
        img_copy.save(out_io, format="PNG", optimize=True)
    else:
        img_copy.convert("RGB").save(out_io, format="JPEG", quality=90, optimize=True)
    return out_io.getvalue()


def fetch_cover_by_isbn(isbn: str, timeout: int = 6) -> bytes | None:
    """
    Fetches book cover bytes for a given ISBN from public book APIs.
    Tries Open Library Covers API first, then Google Books API, and Open Library Search API.
    Returns optimized image bytes or None if not found.
    """
    clean = clean_isbn(isbn)
    if not clean or len(clean) < 9:
        return None

    # 1. Try Open Library Covers API (Large, then Medium)
    for size in ("L", "M"):
        ol_url = f"https://covers.openlibrary.org/b/isbn/{clean}-{size}.jpg?default=false"
        try:
            resp = requests.get(ol_url, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 500:
                with Image.open(io.BytesIO(resp.content)) as img:
                    img.verify()
                return optimize_image_bytes(resp.content)
        except Exception:
            pass

    # 2. Try Google Books API
    gb_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean}"
    try:
        resp = requests.get(gb_url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            for item in items:
                volume_info = item.get("volumeInfo", {})
                img_links = volume_info.get("imageLinks", {})
                img_url = (
                    img_links.get("extraLarge")
                    or img_links.get("large")
                    or img_links.get("medium")
                    or img_links.get("thumbnail")
                    or img_links.get("smallThumbnail")
                )
                if img_url:
                    img_url = img_url.replace("http://", "https://")
                    img_resp = requests.get(img_url, timeout=timeout)
                    if img_resp.status_code == 200 and len(img_resp.content) > 500:
                        with Image.open(io.BytesIO(img_resp.content)) as img:
                            img.verify()
                        return optimize_image_bytes(img_resp.content)
    except Exception:
        pass

    # 3. Fallback: Open Library Search API
    ol_search_url = f"https://openlibrary.org/search.json?isbn={clean}&fields=cover_i"
    try:
        resp = requests.get(ol_search_url, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get("docs", [])
            if docs:
                cover_id = docs[0].get("cover_i")
                if cover_id:
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg?default=false"
                    img_resp = requests.get(cover_url, timeout=timeout)
                    if img_resp.status_code == 200 and len(img_resp.content) > 500:
                        with Image.open(io.BytesIO(img_resp.content)) as img:
                            img.verify()
                        return optimize_image_bytes(img_resp.content)
    except Exception:
        pass

    return None


def clean_search_term(term) -> str:
    """
    Cleans search terms by stripping surrounding quotes, extra punctuation, and whitespace.
    """
    if term is None:
        return ""
    cleaned = str(term).strip()
    cleaned = re.sub(r'[\"\'\`\(\)\[\]\{\}]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def search_covers_by_title_and_author(
    title: str,
    author: str = "",
    isbn: str = "",
    max_results: int = 3,
    timeout: int = 7
) -> list[dict]:
    """
    Searches public book catalogs (Open Library & Google Books) for cover artwork matching
    the provided book title and author name (and optional ISBN).
    Returns a list of up to `max_results` dictionaries containing:
      {
         'title': str,
         'author': str,
         'year': str,
         'source': str,
         'image_bytes': bytes,
         'isbn': str or None
      }
    """
    results = []
    seen_hashes = set()

    clean_t = clean_search_term(title)
    clean_a = clean_search_term(author)
    clean_code = clean_isbn(isbn)

    if not clean_t and not clean_a and not clean_code:
        return results

    # 1. If ISBN is provided, try direct ISBN cover first
    if clean_code:
        direct_bytes = fetch_cover_by_isbn(clean_code, timeout=timeout)
        if direct_bytes:
            h = hashlib.md5(direct_bytes).hexdigest()
            seen_hashes.add(h)
            results.append({
                "title": clean_t or "Matching Edition",
                "author": clean_a or "",
                "year": "",
                "source": "ISBN Match",
                "image_bytes": direct_bytes,
                "isbn": clean_code
            })

    # 2. Search Open Library Search API
    if len(results) < max_results and (clean_t or clean_a):
        try:
            params = {
                "limit": 15,
                "fields": "title,author_name,first_publish_year,cover_i,isbn"
            }
            if clean_t:
                params["title"] = clean_t
            if clean_a:
                params["author"] = clean_a

            ol_resp = requests.get("https://openlibrary.org/search.json", params=params, timeout=timeout)
            if ol_resp.status_code == 200:
                docs = ol_resp.json().get("docs", [])
                for doc in docs:
                    doc_title = doc.get("title") or clean_t
                    auth_list = doc.get("author_name", [])
                    doc_author = ", ".join(auth_list) if isinstance(auth_list, list) else str(auth_list or clean_a)
                    doc_year = str(doc.get("first_publish_year") or "")
                    cover_id = doc.get("cover_i")
                    doc_isbns = doc.get("isbn", [])

                    cover_urls = []
                    if cover_id:
                        cover_urls.append(f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg?default=false")
                        cover_urls.append(f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg?default=false")
                    elif doc_isbns:
                        cover_urls.append(f"https://covers.openlibrary.org/b/isbn/{doc_isbns[0]}-L.jpg?default=false")

                    for url in cover_urls:
                        try:
                            img_resp = requests.get(url, timeout=timeout)
                            if img_resp.status_code == 200 and len(img_resp.content) > 500:
                                opt_bytes = optimize_image_bytes(img_resp.content)
                                h = hashlib.md5(opt_bytes).hexdigest()
                                if h not in seen_hashes:
                                    seen_hashes.add(h)
                                    results.append({
                                        "title": doc_title,
                                        "author": doc_author,
                                        "year": doc_year,
                                        "source": "Open Library",
                                        "image_bytes": opt_bytes,
                                        "isbn": doc_isbns[0] if doc_isbns else None
                                    })
                                    break
                        except Exception:
                            pass

                    if len(results) >= max_results:
                        break
        except Exception as e:
            print("Open Library title/author search error:", e)

    # 3. Fallback / supplementary search with Google Books API
    if len(results) < max_results and (clean_t or clean_a):
        try:
            q_parts = []
            if clean_t:
                q_parts.append(f'intitle:"{clean_t}"')
            if clean_a:
                q_parts.append(f'inauthor:"{clean_a}"')
            q = " ".join(q_parts) if q_parts else f"{clean_t} {clean_a}".strip()

            gb_resp = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": q, "maxResults": 10},
                timeout=timeout
            )
            if gb_resp.status_code == 200:
                items = gb_resp.json().get("items", [])
                for it in items:
                    v = it.get("volumeInfo", {})
                    it_title = v.get("title") or clean_t
                    it_authors = v.get("authors", [])
                    it_author = ", ".join(it_authors) if isinstance(it_authors, list) else str(it_authors or clean_a)
                    pdate = v.get("publishedDate", "")
                    it_year = pdate[:4] if pdate else ""

                    img_links = v.get("imageLinks", {})
                    img_url = (
                        img_links.get("extraLarge")
                        or img_links.get("large")
                        or img_links.get("medium")
                        or img_links.get("thumbnail")
                        or img_links.get("smallThumbnail")
                    )
                    if img_url:
                        img_url = img_url.replace("http://", "https://")
                        try:
                            img_resp = requests.get(img_url, timeout=timeout)
                            if img_resp.status_code == 200 and len(img_resp.content) > 500:
                                opt_bytes = optimize_image_bytes(img_resp.content)
                                h = hashlib.md5(opt_bytes).hexdigest()
                                if h not in seen_hashes:
                                    seen_hashes.add(h)
                                    results.append({
                                        "title": it_title,
                                        "author": it_author,
                                        "year": it_year,
                                        "source": "Google Books",
                                        "image_bytes": opt_bytes,
                                        "isbn": None
                                    })
                                    if len(results) >= max_results:
                                        break
                        except Exception:
                            pass
        except Exception as e:
            print("Google Books title/author search error:", e)

    return results[:max_results]


def auto_fetch_and_save_book_cover(book_id: int, isbn: str = None) -> tuple[bool, str]:
    """
    Retrieves the book's ISBN, queries online APIs for the cover image, and saves to database.
    Returns (success: bool, message: str).
    """
    if isbn is None:
        book_rows = db_get.get_book_by_id(book_id)
        if not book_rows:
            return False, f"Book ID {book_id} not found."
        isbn = book_rows[0][10]

    clean = clean_isbn(isbn)
    if not clean:
        return False, "Book does not have a valid ISBN."

    image_bytes = fetch_cover_by_isbn(clean)
    if image_bytes:
        res = db_update.update_book_cover(book_id, image_bytes)
        if res == "success":
            return True, f"Cover image for ISBN {clean} successfully downloaded and saved."
        else:
            return False, f"Failed to save cover image to database: {res}"
    else:
        return False, f"No cover image found online for ISBN {clean}."


def batch_fetch_covers_for_missing(progress_callback=None, cancel_check=None) -> dict:
    """
    Scans database for all books with an ISBN but missing a cover image, and fetches covers.
    progress_callback: fn(current: int, total: int, title: str, success: bool, msg: str)
    cancel_check: fn() -> bool (returns True if batch should stop)
    Returns: {"total": int, "processed": int, "fetched": int, "failed": int}
    """
    books = db_get.get_books_missing_covers()
    total = len(books)
    result = {
        "total": total,
        "processed": 0,
        "fetched": 0,
        "failed": 0
    }

    if total == 0:
        return result

    for idx, (book_id, title, raw_isbn) in enumerate(books, start=1):
        if cancel_check and cancel_check():
            break

        clean = clean_isbn(raw_isbn)
        success = False
        msg = ""

        if not clean:
            msg = "Invalid ISBN"
            result["failed"] += 1
        else:
            image_bytes = fetch_cover_by_isbn(clean)
            if image_bytes:
                db_res = db_update.update_book_cover(book_id, image_bytes)
                if db_res == "success":
                    success = True
                    result["fetched"] += 1
                    msg = "Cover saved"
                else:
                    result["failed"] += 1
                    msg = f"DB Error: {db_res}"
            else:
                result["failed"] += 1
                msg = "Not found online"

        result["processed"] = idx

        if progress_callback:
            try:
                progress_callback(idx, total, title, success, msg)
            except Exception:
                pass

    return result
