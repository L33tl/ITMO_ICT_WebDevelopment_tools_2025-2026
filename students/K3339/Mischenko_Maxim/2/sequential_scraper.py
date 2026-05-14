import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from typing import List

DB_PATH = "web_scraping.db"

def init_database():
    """Ensure database and table exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS web_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        title TEXT,
        parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def parse_and_save(url: str) -> str:
    """
    Fetch HTML from URL, parse title, save to database, and return result.
    
    Args:
        url: Web page URL to parse
        
    Returns:
        str: Status message with title or error
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "No title"
        if title:
            title = title.strip()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO web_pages (url, title) VALUES (?, ?)",
            (url, title)
        )
        conn.commit()
        conn.close()
        
        result = f"OK: {url[:50]}... -> '{title[:50]}...'"
        print(result)
        return result
        
    except requests.exceptions.RequestException as e:
        error_msg = f"ERROR: {url[:50]}... -> {str(e)[:50]}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"ERROR: {url[:50]}... -> {str(e)[:50]}"
        print(error_msg)
        return error_msg

def main():
    """Main function: sequential scraping."""
    init_database()
    urls = [
        "https://www.python.org",
        "https://www.wikipedia.org",
        "https://www.github.com",
        "https://www.stackoverflow.com",
        "https://www.google.com",
        "https://www.youtube.com",
        "https://www.reddit.com",
        "https://www.amazon.com",
        "https://www.microsoft.com",
        "https://www.apple.com",
        "https://www.linux.org",
        "https://www.djangoproject.com",
        "https://fastapi.tiangolo.com",
        "https://flask.palletsprojects.com",
        "https://www.sqlite.org",
    ]
    
    print(f"Sequential web scraper - Parsing {len(urls)} URLs")
    print("=" * 60)
    
    start_time = time.perf_counter()
    results = []
    for url in urls:
        result = parse_and_save(url)
        results.append(result)
    
    elapsed = time.perf_counter() - start_time
    print("=" * 60)
    print(f"Completed in {elapsed:.2f} seconds")
    success_count = sum(1 for r in results if r and r.startswith("OK"))
    error_count = len(urls) - success_count
    
    print(f"Successfully parsed: {success_count}")
    print(f"Errors: {error_count}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM web_pages")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"Total records in database: {count}")
    
    return elapsed

if __name__ == "__main__":
    main()