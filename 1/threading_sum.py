import threading
import time
from typing import List

N = 10_000_000
NUM_THREADS = 4


def calculate_sum(start: int, end: int) -> int:
    """
    Compute sum of integers from start to end inclusive using a loop.
    This is a CPU-bound task.
    """
    total = 0
    for i in range(start, end + 1):
        total += i
    return total


def worker(start: int, end: int, result_list: List[int], index: int) -> None:
    """
    Worker function to be run in a thread.
    Computes partial sum and stores it in result_list at given index.
    """
    partial = calculate_sum(start, end)
    result_list[index] = partial


def main() -> None:
    print(f"Threading sum from 1 to {N:,} using {NUM_THREADS} threads")
    start_time = time.perf_counter()

    chunk_size = N // NUM_THREADS
    threads = []
    results = [0] * NUM_THREADS

    for i in range(NUM_THREADS):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i < NUM_THREADS - 1 else N
        t = threading.Thread(target=worker, args=(start, end, results, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total = sum(results)
    elapsed = time.perf_counter() - start_time

    print(f"Total sum (threading): {total:,}")
    print(f"Time elapsed: {elapsed:.4f} seconds")

    expected = N * (N + 1) // 2
    if total == expected:
        print("Result is correct.")
    else:
        print(f"Result mismatch! Expected {expected:,}, got {total:,}")


if __name__ == "__main__":
    main()
