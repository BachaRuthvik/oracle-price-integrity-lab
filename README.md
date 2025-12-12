# Oracle Price Integrity Lab

This repository contains small, self-contained experiments around real-time pricing,
oracle-style benchmarks, and anomaly detection in adversarial market conditions.

The goal is to demonstrate how to:
- Aggregate prices across CEX and DEX venues
- Compute stable benchmarks (medians, TWAPs, liquidity-weighted prices)
- Detect anomalies such as staleness, thin liquidity, pool imbalance, and
  flash-loan-style distortions
- Decode on-chain events and reason about swap flows
- Simulate thin-liquidity and flash-loan attacks to stress test detection logic

> Note: All code in this repo uses **synthetic or open data** only. It does not
> contain any proprietary pipelines or production code from past employers.

## Contents

### `src/oracle_anomaly_demo.py`

A small standalone demo that:
- Generates a synthetic multi-venue price + liquidity time series
- Computes a liquidity-weighted benchmark price at each timestamp
- Runs simple detectors for:
  - Staleness
  - Thin-liquidity windows
  - Flash-loan-style jump + reversion patterns
- Prints a timeline showing benchmark price and flags

This script acts as a miniature oracle feed plus anomaly detector loop.

### `src/flashloan_simulator.py`

A thin-liquidity and flash-loan-style manipulation simulator that:
- Implements basic Uniswap v2-style pricing math
- Configures a pool with configurable reserves
- Applies a large, instant swap to simulate a flash-loan attack
- Measures price impact, slippage, and reversion after liquidity is restored

Useful for reasoning about how volatile or adversarial jumps can impact oracle
benchmarks and how to design detection thresholds.

### `src/cex_dex_divergence_monitor.py`

A simple CEX–DEX divergence monitor that:
- Creates a synthetic CEX midprice time series
- Derives a DEX-implied price with noise and occasional distortion
- Computes percentage deviation between CEX and DEX
- Flags windows where divergence exceeds configurable thresholds

This is meant to mimic cross-venue benchmark vs. pool-price deltas and illustrate
how to identify venues that should be down-weighted during stressed conditions.

### `src/swap_trace_decoder.py`

A toy “swap trace decoder” that:
- Accepts a list of synthetic EVM-like log dictionaries
- Filters and classifies SWAP and TRANSFER-style events
- Reconstructs a simplified view of swap flows per pool and token pair

In a real system this would use web3.py and ABIs against real chain data; here
we show the basic parsing and classification logic in a self-contained way.

### `notebooks/notebook_oracle_anomalies.ipynb`

A Jupyter notebook that:
- Reuses the logic from `oracle_anomaly_demo.py`
- Visualizes benchmark price over time with anomaly flags overlaid
- Shows how staleness, thin-liquidity, and flash-like patterns appear in time series

## Getting Started

```bash
git clone <your-repo-url>.git
cd oracle-price-integrity-lab
pip install -r requirements.txt
