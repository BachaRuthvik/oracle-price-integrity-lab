#!/usr/bin/env python3
"""
flashloan_simulator.py

Toy thin-liquidity + flash-loan-style manipulation simulator using
Uniswap v2-style pricing math.

This script:
- sets up an x*y = k pool
- prints initial price
- applies a large swap to simulate an attack
- prints new price and slippage
- "repairs" the pool and prints reversion
"""

import math


def uniswap_v2_price(reserve_in: float, reserve_out: float) -> float:
    """Implied price = reserve_out / reserve_in."""
    return reserve_out / reserve_in


def uniswap_v2_swap(reserve_in: float, reserve_out: float, amount_in: float, fee_bps=30):
    """
    Perform a Uniswap v2-style swap:

    amount_in_with_fee = amount_in * (1 - fee)
    amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)
    """
    fee = fee_bps / 10_000.0
    amount_in_with_fee = amount_in * (1 - fee)
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in + amount_in_with_fee
    amount_out = numerator / denominator

    new_reserve_in = reserve_in + amount_in
    new_reserve_out = reserve_out - amount_out
    return new_reserve_in, new_reserve_out, amount_out


def run_flashloan_demo():
    # Start with a relatively thin pool
    reserve_token = 100.0  # token X
    reserve_usd = 200_000.0  # token Y (e.g., stablecoin)
    print("=== Initial Pool State ===")
    print(f"Reserves: X={reserve_token:.2f}, Y={reserve_usd:.2f}")
    initial_price = uniswap_v2_price(reserve_token, reserve_usd)
    print(f"Initial implied price: 1 X = {initial_price:.2f} Y\n")

    # Simulate a large swap (flash-loan style attack)
    flash_amount_in = 40.0  # big chunk relative to reserves
    print("=== Flash-Loan-Style Swap ===")
    print(f"Attacker swaps {flash_amount_in:.2f} X into the pool.")

    new_reserve_x, new_reserve_y, amount_out_y = uniswap_v2_swap(
        reserve_token, reserve_usd, flash_amount_in
    )
    new_price = uniswap_v2_price(new_reserve_x, new_reserve_y)
    price_impact_pct = (new_price - initial_price) / initial_price * 100.0

    print(f"New reserves: X={new_reserve_x:.2f}, Y={new_reserve_y:.2f}")
    print(f"Attacker received ~{amount_out_y:.2f} Y")
    print(f"New implied price: 1 X = {new_price:.2f} Y")
    print(f"Price impact: {price_impact_pct:.2f}%\n")

    # Now simulate "reversion" – liquidity restored close to original
    print("=== Reversion (Liquidity Restored) ===")
    restored_reserve_x = 100.0
    restored_reserve_y = 200_000.0
    restored_price = uniswap_v2_price(restored_reserve_x, restored_reserve_y)
    revert_pct = (restored_price - new_price) / new_price * 100.0

    print(f"Restored reserves: X={restored_reserve_x:.2f}, Y={restored_reserve_y:.2f}")
    print(f"Restored implied price: 1 X = {restored_price:.2f} Y")
    print(f"Reversion move vs attack price: {revert_pct:.2f}%")
    print(
        "\nThis pattern—a sharp jump from thin liquidity followed by quick reversion—"
        "is what anomaly detectors can use to flag flash-loan-like behavior."
    )


if __name__ == "__main__":
    run_flashloan_demo()
