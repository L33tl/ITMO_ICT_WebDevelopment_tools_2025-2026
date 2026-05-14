import sys
from pathlib import Path
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from celery import Celery
from celery_config import celery_app

sys.path.append(str(Path(__file__).parent))

try:
    from parser_app import parse_and_save
except ImportError:
    def parse_and_save(url: str):
        """
        Fetch HTML from URL, parse title, save to database.
        
        Args:
            url: Web page URL to parse
            
        Returns:
            Dict with parsing results
        """
        DB_PATH = "2/web_scraping.db"
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


@celery_app.task(bind=True, name="parse_url_task")
def parse_url_task(self, url: str):
    """
    Celery task for parsing a URL asynchronously.
    
    Args:
        url: The URL to parse
        
    Returns:
        Dict with parsing results including task_id
    """
    task_id = self.request.id
    
    print(f"Task {task_id}: Starting to parse URL: {url}")
    
    result = parse_and_save(url)
    
    result["task_id"] = task_id
    result["task_status"] = "completed"
    result["completed_at"] = time.time()
    
    if result["status"] == "success":
        print(f"Task {task_id}: Successfully parsed URL: {url}")
    else:
        print(f"Task {task_id}: Failed to parse URL: {url}, error: {result.get('error', 'Unknown error')}")
    
    return result


@celery_app.task(bind=True, name="health_check_task")
def health_check_task(self):
    """
    Health check task for Celery worker.
    
    Returns:
        Dict with health status
    """
    return {
        "status": "healthy",
        "worker": "celery_worker",
        "timestamp": time.time(),
        "task_id": self.request.id
    }


@celery_app.task(bind=True, name="batch_parse_task")
def batch_parse_task(self, urls: list):
    """
    Celery task for parsing multiple URLs in batch.
    
    Args:
        urls: List of URLs to parse
        
    Returns:
        Dict with batch parsing results
    """
    task_id = self.request.id
    results = []
    
    print(f"Task {task_id}: Starting batch parse of {len(urls)} URLs")
    
    for i, url in enumerate(urls):
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1,
                "total": len(urls),
                "status": f"Parsing URL {i + 1} of {len(urls)}"
            }
        )
        
        result = parse_and_save(url)
        result["url"] = url
        results.append(result)
    
    print(f"Task {task_id}: Completed batch parse of {len(urls)} URLs")
    
    return {
        "task_id": task_id,
        "total_urls": len(urls),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "results": results,
        "completed_at": time.time()
    }
