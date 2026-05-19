import sqlite3
import os

DB_PATH = "web_scraping.db"

def init_database():
    """Create database and table if not exists."""
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON web_pages(url)")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")
    print("Table 'web_pages' created with columns: id, url, title, parsed_at")

def clear_database():
    """Clear all data from web_pages table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM web_pages")
    conn.commit()
    conn.close()
    print("Database cleared")

def count_records():
    """Count records in web_pages table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM web_pages")
    count = cursor.fetchone()[0]
    conn.close()
    return count

if __name__ == "__main__":
    init_database()
    print(f"Records in database: {count_records()}")
