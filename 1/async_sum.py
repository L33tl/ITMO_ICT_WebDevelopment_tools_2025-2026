import asyncio
import time

N = 10_000_000
NUM_TASKS = 4


def calculate_sum(start: int, end: int) -> int:
    """
    Compute sum of integers from start to end inclusive using a loop.
    This is a CPU-bound task.
    """
    total = 0
    for i in range(start, end + 1):
        total += i
    return total


async def worker(start: int, end: int) -> int:
    """
    Async worker that runs calculate_sum in a separate thread.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, calculate_sum, start, end)


async def main() -> None:
    print(f"Async sum from 1 to {N:,} using {NUM_TASKS} tasks")
    start_time = time.perf_counter()

    chunk_size = N // NUM_TASKS
    tasks = []
    for i in range(NUM_TASKS):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i < NUM_TASKS - 1 else N
        tasks.append(worker(start, end))

    results = await asyncio.gather(*tasks)

    total = sum(results)
    elapsed = time.perf_counter() - start_time

    print(f"Total sum (async): {total:,}")
    print(f"Time elapsed: {elapsed:.4f} seconds")

    expected = N * (N + 1) // 2
    if total == expected:
        print("Result is correct.")
    else:
        print(f"Result mismatch! Expected {expected:,}, got {total:,}")


if __name__ == "__main__":
    asyncio.run(main())
