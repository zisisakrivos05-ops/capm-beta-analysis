"""Loading price data and computing log returns."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TICKER_NAMES: dict[str, str] = {
    "SPX": "S&P 500",
    "AMZN": "Amazon",
    "STX": "Seagate Technology",
    "F": "Ford Motor",
    "NVDA": "NVIDIA",
    "MSFT": "Microsoft",
}

MARKET = "SPX"


def load_prices(path: str | Path) -> pd.DataFrame:
    """Read a CSV of daily closing prices indexed by date.

    The file must have a ``date`` column and one column per ticker.
    Rows are sorted by date; non-positive or missing prices raise an error,
    because they would make log returns undefined.
    """
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    if df.isna().any().any():
        missing = df.columns[df.isna().any()].tolist()
        raise ValueError(f"Missing prices in columns: {missing}")
    if (df <= 0).any().any():
        raise ValueError("Prices must be strictly positive to compute log returns")
    return df


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily continuously compounded returns: r_t = ln(P_t) - ln(P_{t-1})."""
    return np.log(prices).diff().dropna(how="all")
