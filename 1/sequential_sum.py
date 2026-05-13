import time

N = 10_000_000


def calculate_sum(start: int, end: int) -> int:
    """
    Compute sum of integers from start to end inclusive using a loop.
    """
    total = 0
    for i in range(start, end + 1):
        total += i
    return total


def main() -> None:
    print(f"Sequential sum from 1 to {N:,}")
    start_time = time.perf_counter()

    total = calculate_sum(1, N)
    elapsed = time.perf_counter() - start_time

    print(f"Total sum (sequential): {total:,}")
    print(f"Time elapsed: {elapsed:.4f} seconds")

    expected = N * (N + 1) // 2
    if total == expected:
        print("Result is correct.")
    else:
        print(f"Result mismatch! Expected {expected:,}, got {total:,}")


if __name__ == "__main__":
    main()
