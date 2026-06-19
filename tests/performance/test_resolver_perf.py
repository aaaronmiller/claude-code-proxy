"""Performance tests for ConfigResolver (T082).

T082: 10_000 calls to resolver.resolve() for a hot field; assert p95 < 1 ms.
"""

from __future__ import annotations

import time
import statistics
from src.core.config_resolver import resolver


def test_resolver_perf() -> None:
    # Hot field that exists in schema: assignments.big.model is registered by assignments registry
    field = "assignments.big.model"

    # Ensure resolver is initialized
    resolver._ensure_initialized()

    # Warm-up
    for _ in range(100):
        resolver.resolve(field)

    timings = []
    for _ in range(10_000):
        start = time.perf_counter()
        resolver.resolve(field)
        elapsed_ms = (time.perf_counter() - start) * 1000
        timings.append(elapsed_ms)

    p95 = statistics.quantiles(timings, n=20)[-1]  # 95th percentile (20 -> 0.95)
    assert p95 < 1.0, f"p95 latency {p95:.3f}ms exceeds 1ms threshold"


if __name__ == "__main__":
    test_resolver_perf()
    print("✓ T082 resolver performance test passed (p95 < 1ms)")
