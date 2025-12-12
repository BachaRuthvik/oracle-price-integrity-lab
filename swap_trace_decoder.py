#!/usr/bin/env python3
"""
swap_trace_decoder.py

Toy "swap trace decoder" for synthetic EVM-like logs.

- We define a small set of fake logs representing SWAP and TRANSFER events
- We parse and classify them
- We reconstruct a simple per-pool summary of swap flows

In a real setup, these logs would come from web3.py and ABI decoding.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LogEvent:
    tx_hash: str
    event_type: str  # "SWAP" or "TRANSFER"
    pool: str
    token_in: str
    token_out: str
    amount_in: float
    amount_out: float


def get_synthetic_logs() -> List[Dict]:
    """Return a few synthetic logs that look like decoded on-chain SWAP events."""
    return [
        {
            "tx_hash": "0xabc1",
            "event_type": "SWAP",
            "pool": "POOL_ETH_USDC",
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": 1.2,
            "amount_out": 2400.0,
        },
        {
            "tx_hash": "0xabc2",
            "event_type": "SWAP",
            "pool": "POOL_ETH_USDC",
            "token_in": "USDC",
            "token_out": "ETH",
            "amount_in": 5000.0,
            "amount_out": 2.45,
        },
        {
            "tx_hash": "0xabc3",
            "event_type": "SWAP",
            "pool": "POOL_WBTC_USDC",
            "token_in": "WBTC",
            "token_out": "USDC",
            "amount_in": 0.3,
            "amount_out": 18_000.0,
        },
        {
            "tx_hash": "0xabc4",
            "event_type": "TRANSFER",
            "pool": "POOL_ETH_USDC",
            "token_in": "ETH",
            "token_out": "ETH",
            "amount_in": 0.5,
            "amount_out": 0.5,
        },
    ]


def parse_logs(raw_logs: List[Dict]) -> List[LogEvent]:
    events: List[LogEvent] = []
    for r in raw_logs:
        if r["event_type"] not in ("SWAP", "TRANSFER"):
            continue
        events.append(
            LogEvent(
                tx_hash=r["tx_hash"],
                event_type=r["event_type"],
                pool=r["pool"],
                token_in=r["token_in"],
                token_out=r["token_out"],
                amount_in=float(r["amount_in"]),
                amount_out=float(r["amount_out"]),
            )
        )
    return events


def summarize_swaps(events: List[LogEvent]):
    """
    Build a simple per-pool summary of net flows,
    ignoring TRANSFER events for now.
    """
    summary = defaultdict(lambda: defaultdict(float))

    for e in events:
        if e.event_type != "SWAP":
            continue
        key = e.pool
        summary[key][f"{e.token_in}_sold"] += e.amount_in
        summary[key][f"{e.token_out}_bought"] += e.amount_out

    return summary


def run_decoder():
    raw_logs = get_synthetic_logs()
    events = parse_logs(raw_logs)
    summary = summarize_swaps(events)

    print("\n=== Swap Trace Decoder (Synthetic Logs) ===\n")
    print("Events:")
    for e in events:
        print(
            f"{e.tx_hash}  {e.event_type}  pool={e.pool}  "
            f"{e.amount_in} {e.token_in} -> {e.amount_out} {e.token_out}"
        )

    print("\nPer-pool summary (net flows from SWAP events):\n")
    for pool, stats in summary.items():
        print(f"{pool}:")
        for k, v in stats.items():
            print(f"  {k}: {v:.4f}")
    print()


if __name__ == "__main__":
    run_decoder()
