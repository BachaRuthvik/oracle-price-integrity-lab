#!/usr/bin/env python3
"""
oracle_anomaly_demo.py

Small standalone demo for oracle anomaly detection:
- builds a synthetic CEX/DEX price + liquidity time series
- computes a simple liquidity-weighted benchmark
- runs detectors for:
    * staleness
    * thin-liquidity spikes
    * flash-loan-style jump + reversion
"""

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np


@dataclass
class VenuePoint:
    ts: datetime
    venue: str
    price: float
    liquidity: float  # arbitrary units


@dataclass
class BenchmarkPoint:
    ts: datetime
    benchmark_price: float
    staleness_flag: bool
    thin_liquidity_flag: bool
    flash_loan_flag: bool


def generate_synthetic_series(
    start: datetime,
    n_points: int,
    base_price: float = 2000.0,
    drift_per_step: float = 0.2,
    noise_std: float = 3.0,
) -> List[VenuePoint]:
    """Generate a simple synthetic 3-venue time series with one flash-loan-style spike."""

    venues = ["CEX_A", "CEX_B", "DEX_POOL"]
    results: List[VenuePoint] = []

    price = base_price

    # pick one index range to simulate a flash-loan distortion on DEX_POOL
    flash_start = int(n_points * 0.55)
    flash_end = flash_start + 3  # short-lived spike

    for i in range(n_points):
        # simple drift + noise
        price += drift_per_step + random.gauss(0, noise_std)
        ts = start + timedelta(seconds=i * 10)

        for v in venues:
            p = price

            # venue-specific micro-noise
            if v == "CEX_A":
                p += random.gauss(0, 1.5)
                liquidity = random.uniform(800_000, 1_200_000)
            elif v == "CEX_B":
                p += random.gauss(0, 2.0)
                liquidity = random.uniform(400_000, 800_000)
            else:  # DEX_POOL
                p += random.gauss(0, 3.0)
                liquidity = random.uniform(150_000, 350_000)

                # inject flash-loan-style spike on DEX_POOL
                if flash_start <= i <= flash_end:
                    p *= 1.12  # big temporary jump
                    liquidity = random.uniform(30_000, 60_000)  # drained pool

            results.append(VenuePoint(ts=ts, venue=v, price=p, liquidity=liquidity))

    return results


def compute_liquidity_weighted_benchmark(
    points: List[VenuePoint],
) -> Tuple[float, float]:
    """Return (benchmark_price, total_liquidity) for a set of venue points at a given timestamp."""

    prices = np.array([p.price for p in points], dtype=float)
    liqs = np.array([p.liquidity for p in points], dtype=float)

    if liqs.sum() <= 0:
        return float("nan"), 0.0

    weights = liqs / liqs.sum()
    benchmark = float((weights * prices).sum())
    total_liq = float(liqs.sum())
    return benchmark, total_liq


def detect_staleness(
    current_ts: datetime,
    last_update_ts: datetime,
    max_staleness_seconds: int = 40,
) -> bool:
    """Flag if current_ts - last_update_ts exceeds threshold."""
    return (current_ts - last_update_ts).total_seconds() > max_staleness_seconds


def detect_thin_liquidity(
    total_liquidity: float,
    rolling_liquidity: List[float],
    quantile_threshold: float = 0.2,
) -> bool:
    """
    Flag if current liquidity falls below a rolling quantile (e.g. bottom 20%).
    This is a simple adaptive detector.
    """
    if len(rolling_liquidity) < 10:
        return False

    q = float(np.quantile(rolling_liquidity, quantile_threshold))
    return total_liquidity < q


def detect_flash_loan_pattern(
    recent_benchmarks: List[float],
    spike_threshold_pct: float = 4.0,
) -> bool:
    """
    Simple flash-loan pattern detector:
    - large jump vs previous value
    - followed by reversion toward prior level within a few steps

    This is a toy offline approximation; in a real engine, you would also
    observe the path *after* the spike.
    """
    if len(recent_benchmarks) < 3:
        return False

    prev_prev, prev, current = recent_benchmarks[-3:]
    if math.isnan(prev_prev) or math.isnan(prev) or math.isnan(current):
        return False

    # pct change from prev_prev -> current
    jump_pct = (current - prev_prev) / prev_prev * 100.0
    if jump_pct < spike_threshold_pct:
        return False

    # In this simplified version we approximate reversion by checking that
    # prev is closer to baseline than current.
    revert_toward_prev = abs(prev - prev_prev) < abs(current - prev_prev)
    return revert_toward_prev


def run_demo():
    start = datetime.utcnow().replace(microsecond=0)
    series = generate_synthetic_series(start=start, n_points=60)

    # group by timestamp
    points_by_ts = {}
    for p in series:
        points_by_ts.setdefault(p.ts, []).append(p)

    sorted_ts = sorted(points_by_ts.keys())

    benchmark_history: List[BenchmarkPoint] = []
    rolling_liq: List[float] = []
    rolling_benchmarks: List[float] = []
    last_update_ts = None

    for ts in sorted_ts:
        venue_points = points_by_ts[ts]
        benchmark_price, total_liq = compute_liquidity_weighted_benchmark(venue_points)

        if last_update_ts is None:
            last_update_ts = ts

        staleness_flag = detect_staleness(ts, last_update_ts)
        rolling_liq.append(total_liq)
        thin_liq_flag = detect_thin_liquidity(total_liq, rolling_liq)

        rolling_benchmarks.append(benchmark_price)
        flash_flag = detect_flash_loan_pattern(rolling_benchmarks)

        # Update last_update_ts if we had a valid benchmark
        if not math.isnan(benchmark_price):
            last_update_ts = ts

        benchmark_history.append(
            BenchmarkPoint(
                ts=ts,
                benchmark_price=benchmark_price,
                staleness_flag=staleness_flag,
                thin_liquidity_flag=thin_liq_flag,
                flash_loan_flag=flash_flag,
            )
        )

    print("\n=== Oracle Anomaly Demo: Summary ===\n")
    for bp in benchmark_history:
        flags = []
        if bp.staleness_flag:
            flags.append("STALE")
        if bp.thin_liquidity_flag:
            flags.append("THIN_LIQ")
        if bp.flash_loan_flag:
            flags.append("FLASH_PATTERN")

        flag_str = ", ".join(flags) if flags else "-"
        print(
            f"{bp.ts.isoformat()}  price={bp.benchmark_price:8.2f}  flags=[{flag_str}]"
        )

    print("\nDone. You can now port this logic into notebooks or hook it into monitoring.\n")


if __name__ == "__main__":
    run_demo()
