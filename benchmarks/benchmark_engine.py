#!/usr/bin/env python3
"""Repeatable, non-gating NEXUS simulation scaling benchmark.

Reports wall-clock step latency for fixed seeded worlds. Results are machine-
specific; compare runs on the same runner/runtime for meaningful regressions.
"""
from __future__ import annotations

import argparse
import statistics
import time

from backend import Engine


def benchmark(population: int, steps: int, warmup: int) -> dict:
    engine = Engine(seed=20261031, config={"max_organisms": max(5000, population + 32)})
    # Deterministically spread added organisms across the world.
    for i in range(max(0, population - len(engine.organisms))):
        x = float((i * 37) % (engine.config["world_width"] - 2) + 1)
        y = float(engine.config["world_height"] * (0.82 + ((i * 13) % 17) / 100))
        engine.add("reef_fish", x, y, vx=0.1, vy=0.0)

    for _ in range(warmup):
        engine.step(1 / 30)

    samples = []
    for _ in range(steps):
        start = time.perf_counter()
        engine.step(1 / 30)
        samples.append((time.perf_counter() - start) * 1000)

    ordered = sorted(samples)
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
    mean = statistics.fmean(samples)
    return {
        "population": population,
        "alive": sum(o.alive for o in engine.organisms),
        "mean_ms": mean,
        "median_ms": statistics.median(samples),
        "p95_ms": p95,
        "steps_per_second": 1000 / mean if mean else float("inf"),
        "budget_pct": mean / (1000 / 30) * 100,
        "slowest_stage": engine.performance.get("slowest_stage", "unknown"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--populations", default="20,200,500,1000")
    args = parser.parse_args()
    if args.steps < 1 or args.warmup < 0:
        parser.error("--steps must be positive and --warmup non-negative")

    print("NEXUS AQUARIUM ENGINE BENCHMARK")
    print(f"steps={args.steps} warmup={args.warmup} fixed_dt={1/30:.6f}s")
    print("population | alive | mean ms | median ms | p95 ms | steps/s | 30fps budget")
    print("-" * 86)
    for count in (int(v.strip()) for v in args.populations.split(",") if v.strip()):
        result = benchmark(count, args.steps, args.warmup)
        print(
            f"{result['population']:10d} | {result['alive']:5d} | "
            f"{result['mean_ms']:7.2f} | {result['median_ms']:9.2f} | "
            f"{result['p95_ms']:6.2f} | {result['steps_per_second']:7.1f} | "
            f"{result['budget_pct']:6.1f}%"
        )
    print("Note: timings depend on runner hardware and Python version; this is not a mobile-device benchmark.")


if __name__ == "__main__":
    main()
