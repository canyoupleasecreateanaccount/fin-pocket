"""Shared test fixtures for fin-pocket tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """Generate a realistic OHLCV DataFrame with 200 bars for testing."""
    np.random.seed(42)
    n = 200
    dates = pd.bdate_range(start="2024-01-02", periods=n)

    close = 100.0
    closes = []
    for _ in range(n):
        close *= 1 + np.random.normal(0.0005, 0.015)
        closes.append(close)

    closes = np.array(closes)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.008, n)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.008, n)))
    opens = lows + (highs - lows) * np.random.uniform(0.2, 0.8, n)
    volumes = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes,
        },
        index=dates,
    )


@pytest.fixture
def trending_up_ohlcv() -> pd.DataFrame:
    """Generate an uptrending OHLCV DataFrame (clear bull run then consolidation)."""
    np.random.seed(7)
    n = 150
    dates = pd.bdate_range(start="2024-01-02", periods=n)

    close = 100.0
    closes = []
    for i in range(n):
        if i < 40:
            close *= 1 + np.random.normal(0.005, 0.008)
        elif i < 80:
            close *= 1 + np.random.normal(-0.002, 0.006)
        else:
            close *= 1 + np.random.normal(0.003, 0.01)
        closes.append(close)

    closes = np.array(closes)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.006, n)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.006, n)))
    opens = lows + (highs - lows) * np.random.uniform(0.3, 0.7, n)
    volumes = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes,
        },
        index=dates,
    )


@pytest.fixture
def short_ohlcv() -> pd.DataFrame:
    """Generate a minimal OHLCV DataFrame (20 bars) for edge-case tests."""
    np.random.seed(99)
    n = 20
    dates = pd.bdate_range(start="2024-06-01", periods=n)

    closes = 50.0 + np.cumsum(np.random.normal(0, 0.5, n))
    highs = closes + np.abs(np.random.normal(0, 0.3, n))
    lows = closes - np.abs(np.random.normal(0, 0.3, n))
    opens = lows + (highs - lows) * 0.5
    volumes = np.random.randint(500_000, 5_000_000, n)

    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes,
        },
        index=dates,
    )
