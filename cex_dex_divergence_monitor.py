#!/usr/bin/env python3
"""
cex_dex_divergence_monitor.py

Simple synthetic CEX–DEX divergence monitor.

- Creates a synthetic CEX price series as a baseline
- Creates a DEX-implied price series with noise and occasional distortions
- Computes percentage deviation (DEX vs CEX)
- Flags timesteps where divergence exceeds thresholds
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

import numpy as np


@dataclass
class DivergencePoint:
    ts: datetime
    cex_price: float
    dex_price: float
    deviation_pct: float
    flagged: bool


def generate_cex_dex_series(
    n_points: int,
    base_price: float = 2000.0,
    drift: float = 0.1,
    noise_cex: float = 2.0,
    noise_dex: float = 4.0,
    distortion_prob: float = 0.08,
    distortion_magnitude_pct: float = 5.0,
):
    start = datetime.utcnow().replace(microsecond=0)
    cex_prices = []
    dex_prices = []
    ts_list = []

    price = base_price
    for i in range(n_points):
        price += drift + np.random.normal(0, noise_cex)
        ts = start + timedelta(seconds=i * 20)

        cex_price = price + np.random.normal(0, noise_cex)
        dex_price = price + np.random.normal(0, noise_dex)

        # occasional distortion on DEX side to simulate thin-liquidity or manipulation
        if np.random.rand() < distortion_prob:
            sign = np.random.choice([-1, 1])
            dex_price *= 1 + sign * (distortion_magnitude_pct / 100.0)

        cex_prices.append(cex_price)
        dex_prices.append(dex_price)
        ts_list.append(ts)

    return ts_list, np.array(cex_prices), np.array(dex_prices)


def compute_divergence_points(
    ts_list: List[datetime],
    cex_prices,
    dex_prices,
    warn_threshold_pct: float = 1.5,
):
    points: List[DivergencePoint] = []
    for ts, cp, dp in zip(ts_list, cex_prices, dex_prices):
        deviation_pct = (dp - cp) / cp * 100.0
        flagged = abs(deviation_pct) >= warn_threshold_pct
        points.append(
            DivergencePoint(
                ts=ts,
                cex_price=float(cp),
                dex_price=float(dp),
                deviation_pct=float(deviation_pct),
                flagged=flagged,
            )
        )
    return points


def run_monitor():
    ts_list, cex_prices, dex_prices = generate_cex_dex_series(n_points=50)
    points = compute_divergence_points(ts_list, cex_prices, dex_prices)

    print("\n=== CEX–DEX Divergence Monitor (Synthetic) ===\n")
    for p in points:
        marker = "FLAG" if p.flagged else "OK"
        print(
            f"{p.ts.isoformat()}  CEX={p.cex_price:8.2f}  "
            f"DEX={p.dex_price:8.2f}  dev={p.deviation_pct:6.2f}%  [{marker}]"
        )

    num_flagged = sum(1 for p in points if p.flagged)
    print(f"\nFlagged {num_flagged} / {len(points)} points above threshold.\n")


if __name__ == "__main__":
    run_monitor()
