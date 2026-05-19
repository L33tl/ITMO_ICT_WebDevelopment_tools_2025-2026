import subprocess
import sys
import time
import sqlite3
import os

DB_PATH = "web_scraping.db"

def clear_database():
    """Clear the database before each test for fair comparison."""
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM web_pages")
        conn.commit()
        conn.close()
        print("Database cleared for fresh test")
    else:
        print("Database does not exist, will be created")

def run_script(script_name: str) -> float:
    """
    Run a Python script and extract its execution time from output.
    
    Args:
        script_name: Name of the script to run
        
    Returns:
        float: Execution time in seconds, or -1 if failed
    """
    print(f"\n{'='*60}")
    print(f"Running {script_name}...")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        for line in result.stdout.split('\n'):
            if "Completed in" in line:
                parts = line.split()
                for part in parts:
                    if part.replace('.', '').isdigit():
                        try:
                            return float(part)
                        except ValueError:
                            continue
        return -1
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: {script_name} timed out after 2 minutes")
        return -1
    except Exception as e:
        print(f"ERROR running {script_name}: {e}")
        return -1

def count_database_records():
    """Count records in database."""
    if not os.path.exists(DB_PATH):
        return 0
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM web_pages")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def main():
    """Main comparison function."""
    print("Web Scraping Performance Comparison")
    print("=" * 60)
    print("Comparing sequential, threading, multiprocessing, and async approaches")
    print()
    clear_database()
    scripts = [
        ("sequential_scraper.py", "Sequential"),
        ("threading_scraper.py", "Threading"),
        ("multiprocessing_scraper.py", "Multiprocessing"),
        ("async_scraper.py", "Async"),
    ]
    
    results = {}
    
    for script_file, approach in scripts:
        if approach != "Sequential":
            clear_database()
        
        time_taken = run_script(script_file)
        record_count = count_database_records()
        
        results[approach] = {
            "time": time_taken,
            "records": record_count
        }
        time.sleep(1)
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON RESULTS")
    print("="*60)
    print(f"{'Approach':<20} {'Time (s)':<12} {'Records':<10} {'Speedup':<10}")
    print("-"*60)
    sequential_time = results.get("Sequential", {}).get("time", 0)
    if sequential_time > 0:
        for approach, data in results.items():
            time_val = data["time"]
            records = data["records"]
            if time_val > 0:
                speedup = sequential_time / time_val
                print(f"{approach:<20} {time_val:<12.2f} {records:<10} {speedup:<10.2f}x")
            else:
                print(f"{approach:<20} {'ERROR':<12} {records:<10} {'N/A':<10}")
    else:
        for approach, data in results.items():
            time_val = data["time"]
            records = data["records"]
            print(f"{approach:<20} {time_val:<12.2f} {records:<10} {'N/A':<10}")
    
    print("="*60)
    print("\nANALYSIS:")
    print("-"*60)
    
    if sequential_time > 0:
        fastest_approach = min(
            [(k, v["time"]) for k, v in results.items() if v["time"] > 0],
            key=lambda x: x[1],
            default=("None", 0)
        )
        
        print(f"Fastest approach: {fastest_approach[0]} ({fastest_approach[1]:.2f}s)")
        print(f"Sequential baseline: {sequential_time:.2f}s")
        
        if fastest_approach[0] != "Sequential":
            speedup = sequential_time / fastest_approach[1]
            print(f"Speedup over sequential: {speedup:.2f}x")

if __name__ == "__main__":
    main()
