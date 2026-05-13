import asyncio
import aiohttp
import sqlite3
import time
from bs4 import BeautifulSoup
from typing import List
import aiosqlite

DB_PATH = "web_scraping.db"

async def init_database():
    """Ensure database and table exist."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS web_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT,
            parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await conn.commit()

async def save_to_database(url: str, title: str):
    """Save URL and title to database asynchronously."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO web_pages (url, title) VALUES (?, ?)",
            (url, title)
        )
        await conn.commit()

async def parse_and_save(url: str, session: aiohttp.ClientSession) -> str:
    """
    Fetch HTML from URL, parse title, save to database, and return result.
    
    Args:
        url: Web page URL to parse
        session: aiohttp ClientSession
        
    Returns:
        str: Status message with title or error
    """
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No title"
        if title:
            title = title.strip()
        await save_to_database(url, title)
        
        result = f"OK: {url[:50]}... -> '{title[:50]}...'"
        print(result)
        return result
        
    except aiohttp.ClientError as e:
        error_msg = f"ERROR: {url[:50]}... -> {str(e)[:50]}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"ERROR: {url[:50]}... -> {str(e)[:50]}"
        print(error_msg)
        return error_msg

async def worker(urls: List[str]) -> List[str]:
    """
    Worker coroutine: processes a list of URLs concurrently.
    
    Args:
        urls: List of URLs to process
        
    Returns:
        List[str]: Results for each URL
    """
    connector = aiohttp.TCPConnector(limit_per_host=5, limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [parse_and_save(url, session) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

async def main():
    """Main async function: parallel scraping using asyncio."""
    await init_database()
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
    
    print(f"Async web scraper - Parsing {len(urls)} URLs")
    print("=" * 60)
    CONCURRENT_TASKS = 10  # Number of concurrent requests
    chunk_size = (len(urls) + CONCURRENT_TASKS - 1) // CONCURRENT_TASKS
    chunks = []
    for i in range(0, len(urls), chunk_size):
        chunks.append(urls[i:i + chunk_size])
    
    start_time = time.perf_counter()
    all_results = []
    for chunk in chunks:
        chunk_results = await worker(chunk)
        all_results.extend(chunk_results)
    
    elapsed = time.perf_counter() - start_time
    print("=" * 60)
    print(f"Completed in {elapsed:.2f} seconds")
    success_count = sum(1 for r in all_results if r and r.startswith("OK"))
    error_count = len(urls) - success_count
    
    print(f"Successfully parsed: {success_count}")
    print(f"Errors: {error_count}")
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM web_pages")
        count = (await cursor.fetchone())[0]
    
    print(f"Total records in database: {count}")
    
    return elapsed

def run_main():
    """Run the async main function."""
    return asyncio.run(main())

if __name__ == "__main__":
    run_main()