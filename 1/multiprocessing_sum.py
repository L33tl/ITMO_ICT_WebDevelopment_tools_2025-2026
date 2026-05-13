import multiprocessing
import time
from typing import List

N = 10_000_000  # Total numbers to sum (1 to N)
NUM_PROCESSES = 4  # Number of processes to use


def calculate_sum(start: int, end: int) -> int:
    """
    Compute sum of integers from start to end inclusive using a loop.
    This is a CPU-bound task.
    """
    total = 0
    for i in range(start, end + 1):
        total += i
    return total


def worker(args) -> int:
    """
    Worker function to be run in a process.
    Returns partial sum.
    """
    start, end = args
    return calculate_sum(start, end)


def main() -> None:
    print(f"Multiprocessing sum from 1 to {N:,} using {NUM_PROCESSES} processes")
    start_time = time.perf_counter()
    chunk_size = N // NUM_PROCESSES
    tasks = []
    for i in range(NUM_PROCESSES):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i < NUM_PROCESSES - 1 else N
        tasks.append((start, end))
    with multiprocessing.Pool(processes=NUM_PROCESSES) as pool:
        results = pool.map(worker, tasks)

    total = sum(results)
    elapsed = time.perf_counter() - start_time

    print(f"Total sum (multiprocessing): {total:,}")
    print(f"Time elapsed: {elapsed:.4f} seconds")
    expected = N * (N + 1) // 2
    if total == expected:
        print("Result is correct.")
    else:
        print(f"Result mismatch! Expected {expected:,}, got {total:,}")


if __name__ == "__main__":
    main()
