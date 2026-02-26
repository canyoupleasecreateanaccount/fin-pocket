"""Tests for Double Top/Bottom signal."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.double_top_bottom import DoubleTopBottom


def _make_double_bottom(n: int = 200) -> pd.DataFrame:
    """Generate data with a clear double bottom pattern."""
    np.random.seed(10)
    dates = pd.bdate_range("2024-01-02", periods=n)

    closes = []
    price = 100.0
    for i in range(n):
        if i < 40:
            price *= 1 + np.random.normal(-0.004, 0.006)
        elif i < 60:
            price *= 1 + np.random.normal(0.005, 0.006)
        elif i < 100:
            price *= 1 + np.random.normal(-0.004, 0.006)
        else:
            price *= 1 + np.random.normal(0.003, 0.008)
        closes.append(price)

    closes = np.array(closes)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.005, n)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.005, n)))
    opens = lows + (highs - lows) * np.random.uniform(0.3, 0.7, n)
    volumes = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=dates,
    )


def _make_double_top(n: int = 200) -> pd.DataFrame:
    """Generate data with a clear double top pattern (deterministic)."""
    dates = pd.bdate_range("2024-01-02", periods=n)
    np.random.seed(42)
    noise = np.random.normal(0, 0.3, n)

    closes = np.empty(n)
    for i in range(n):
        if i < 30:
            closes[i] = 100 + i * 0.8 + noise[i]
        elif i < 50:
            closes[i] = 124 + noise[i]
        elif i < 70:
            closes[i] = 124 - (i - 50) * 0.6 + noise[i]
        elif i < 90:
            closes[i] = 112 + (i - 70) * 0.6 + noise[i]
        elif i < 110:
            closes[i] = 124 + noise[i]
        else:
            closes[i] = 124 - (i - 110) * 0.5 + noise[i]

    highs = closes + np.abs(np.random.normal(0.5, 0.3, n))
    lows = closes - np.abs(np.random.normal(0.5, 0.3, n))
    opens = lows + (highs - lows) * np.random.uniform(0.3, 0.7, n)
    volumes = np.random.randint(1_000_000, 10_000_000, n)

    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=dates,
    )


class TestDoubleTopBottom:
    def test_calculate_returns_dataframe(self, sample_ohlcv):
        dtb = DoubleTopBottom()
        result = dtb.calculate(sample_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_name(self):
        dtb = DoubleTopBottom()
        assert dtb.name == "Double Top/Bottom"

    def test_panel_is_main(self):
        dtb = DoubleTopBottom()
        assert dtb.panel == "main"

    def test_does_not_modify_input(self, sample_ohlcv):
        dtb = DoubleTopBottom()
        original = sample_ohlcv.copy()
        dtb.calculate(sample_ohlcv)
        pd.testing.assert_frame_equal(sample_ohlcv, original)

    def test_custom_params(self):
        dtb = DoubleTopBottom(
            lookback=5, tolerance_pct=3.0, min_distance=10,
            max_distance=80, min_depth_pct=2.0, recent_bars=200,
        )
        assert dtb.lookback == 5
        assert dtb.tolerance_pct == 3.0

    def test_plot_returns_figure(self, sample_ohlcv):
        dtb = DoubleTopBottom()
        dtb.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        result = dtb.plot(fig, sample_ohlcv, row=1)
        assert isinstance(result, go.Figure)

    def test_no_crash_on_short_data(self, short_ohlcv):
        dtb = DoubleTopBottom()
        result = dtb.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_no_crash_on_flat_data(self):
        n = 100
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [50.0]*n, "High": [50.0]*n, "Low": [50.0]*n,
             "Close": [50.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        dtb = DoubleTopBottom()
        result = dtb.calculate(df)
        assert isinstance(result, pd.DataFrame)
        assert len(dtb._patterns) == 0

    def test_detects_double_bottom(self):
        df = _make_double_bottom()
        dtb = DoubleTopBottom(min_depth_pct=2.0, tolerance_pct=4.0)
        dtb.calculate(df)
        bottoms = [p for p in dtb._patterns if p["type"] == "double_bottom"]
        assert len(bottoms) >= 1

    def test_detects_double_top(self):
        df = _make_double_top()
        dtb = DoubleTopBottom(min_depth_pct=2.0, tolerance_pct=4.0)
        dtb.calculate(df)
        tops = [p for p in dtb._patterns if p["type"] == "double_top"]
        assert len(tops) >= 1

    def test_pattern_has_required_keys(self):
        df = _make_double_bottom()
        dtb = DoubleTopBottom(min_depth_pct=2.0, tolerance_pct=4.0)
        dtb.calculate(df)
        if dtb._patterns:
            p = dtb._patterns[0]
            for key in ["type", "idx1", "idx2", "val1", "val2",
                        "neckline", "depth_pct", "confirmed",
                        "date1", "date2"]:
                assert key in p, f"Missing key: {key}"

    def test_plot_with_patterns(self):
        df = _make_double_bottom()
        dtb = DoubleTopBottom(min_depth_pct=2.0, tolerance_pct=4.0)
        dtb.calculate(df)
        fig = make_subplots(rows=1, cols=1)
        result = dtb.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)
        if dtb._patterns:
            assert len(fig.data) > 0
