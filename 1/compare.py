import subprocess
import re
import time

SCRIPTS = [
    ("Sequential", "sequential_sum.py"),
    ("Threading", "threading_sum.py"),
    ("Multiprocessing", "multiprocessing_sum.py"),
    ("Async", "async_sum.py"),
]

TIME_PATTERN = re.compile(r"Time elapsed: ([\d.]+) seconds")


def run_script(name: str, script_path: str) -> float:
    """
    Run a Python script and extract the elapsed time from its output.
    Returns elapsed time in seconds.
    """
    print(f"Running {name}...")
    start = time.perf_counter()
    result = subprocess.run(
        ["python3", script_path],
        capture_output=True,
        text=True,
        cwd="."
    )
    end = time.perf_counter()
    wall_time = end - start  # wall-clock time
    output = result.stdout + result.stderr
    match = TIME_PATTERN.search(output)
    if match:
        elapsed = float(match.group(1))
        print(f"  -> Script reported time: {elapsed:.4f}s, wall time: {wall_time:.4f}s")
        return elapsed
    else:
        print(f"  -> Could not parse time, using wall time: {wall_time:.4f}s")
        return wall_time


def main():
    print("=" * 60)
    print("Performance Comparison of Parallel Sum Implementations")
    print("=" * 60)
    print()

    results = []
    for name, script in SCRIPTS:
        elapsed = run_script(name, script)
        results.append((name, elapsed))
        print()
    results.sort(key=lambda x: x[1])

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Approach':<20} {'Time (s)':<12} {'Speedup':<10}")
    print("-" * 60)
    baseline = results[0][1]  # fastest time
    for name, elapsed in results:
        speedup = baseline / elapsed if elapsed > 0 else float('inf')
        print(f"{name:<20} {elapsed:<12.4f} {speedup:<10.2f}")
    seq_time = next(t for n, t in results if n == "Sequential")
    print("\nSpeedup relative to Sequential:")
    for name, elapsed in results:
        if name != "Sequential":
            speedup = seq_time / elapsed
            print(f"  {name}: {speedup:.2f}x")

    print("\nConclusion:")
    print("Multiprocessing should be fastest for CPU-bound tasks due to GIL.")
    print("Threading may have overhead due to GIL contention.")
    print("Async with thread pool adds overhead but still concurrent.")
    print("Sequential is baseline.")


if __name__ == "__main__":
    main()