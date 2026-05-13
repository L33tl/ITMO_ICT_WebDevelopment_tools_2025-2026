import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "2"))

from fastapi import FastAPI, HTTPException
import requests
from typing import Dict, Any
import sqlite3
from bs4 import BeautifulSoup
import time

app = FastAPI(title="Web Parser API", description="HTTP interface for web parsing functionality")

DB_PATH = "2/web_scraping.db"

def init_parser_database():
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

@app.on_event("startup")
def on_startup():
    """Initialize parser database on startup."""
    init_parser_database()
    print("Parser database initialized")

def parse_and_save(url: str) -> Dict[str, Any]:
    """
    Fetch HTML from URL, parse title, save to database.
    
    Args:
        url: Web page URL to parse
        
    Returns:
        Dict with parsing results
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
        
        return {
            "status": "success",
            "url": url,
            "title": title,
            "message": f"Successfully parsed: {title[:50]}..."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "url": url,
            "error": str(e),
            "message": f"Failed to parse URL: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "error": str(e),
            "message": f"Unexpected error: {str(e)}"
        }

@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Web Parser API",
        "endpoints": {
            "parse": "POST /parse - Parse a URL",
            "health": "GET /health - Health check",
            "stats": "GET /stats - Get parsing statistics"
        }
    }

@app.post("/parse")
def parse_url(url: str):
    """
    Parse a given URL and save results to database.
    
    Args:
        url: The URL to parse (query parameter)
        
    Returns:
        Parsing results
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    result = parse_and_save(url)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/stats")
def get_stats():
    """Get parsing statistics from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM web_pages")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT url) FROM web_pages")
        unique = cursor.fetchone()[0]
        
        cursor.execute("SELECT url, title, parsed_at FROM web_pages ORDER BY parsed_at DESC LIMIT 10")
        recent = cursor.fetchall()
        conn.close()
        
        return {
            "total_parsed": total,
            "unique_urls": unique,
            "recent_parses": [
                {"url": row[0], "title": row[1], "parsed_at": row[2]}
                for row in recent
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
