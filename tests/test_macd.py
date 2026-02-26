"""Tests for MACD signal."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.macd import MACD


class TestMACD:
    def test_calculate_adds_columns(self, sample_ohlcv):
        macd = MACD()
        result = macd.calculate(sample_ohlcv)
        assert "MACD" in result.columns
        assert "MACD_signal" in result.columns
        assert "MACD_hist" in result.columns
        assert "MACD_bull_cross" in result.columns
        assert "MACD_bear_cross" in result.columns

    def test_histogram_is_difference(self, sample_ohlcv):
        macd = MACD()
        result = macd.calculate(sample_ohlcv)
        diff = result["MACD"] - result["MACD_signal"]
        pd.testing.assert_series_equal(result["MACD_hist"], diff, check_names=False)

    def test_crossover_detection(self):
        n = 60
        dates = pd.bdate_range("2024-01-02", periods=n)
        prices = np.concatenate([
            np.linspace(100, 120, 30),
            np.linspace(120, 95, 30),
        ])
        df = pd.DataFrame(
            {"Open": prices, "High": prices + 1, "Low": prices - 1,
             "Close": prices, "Volume": [1_000_000] * n},
            index=dates,
        )
        macd = MACD()
        result = macd.calculate(df)
        assert result["MACD_bull_cross"].any() or result["MACD_bear_cross"].any()

    def test_plot_with_crossovers(self):
        n = 60
        dates = pd.bdate_range("2024-01-02", periods=n)
        prices = np.concatenate([
            np.linspace(100, 130, 30),
            np.linspace(130, 90, 30),
        ])
        df = pd.DataFrame(
            {"Open": prices, "High": prices + 1, "Low": prices - 1,
             "Close": prices, "Volume": [1_000_000] * n},
            index=dates,
        )
        macd = MACD()
        result = macd.calculate(df)
        fig = make_subplots(rows=2, cols=1)
        macd.plot(fig, result, row=1)
        trace_names = [t.name for t in fig.data]
        assert "MACD Hist" in trace_names
        assert "MACD" in trace_names
        assert "Signal" in trace_names

    def test_plot_no_crossovers(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        macd = MACD()
        result = macd.calculate(df)
        fig = make_subplots(rows=2, cols=1)
        macd.plot(fig, result, row=1)
        trace_names = [t.name for t in fig.data]
        assert "MACD Bull Cross" not in trace_names
        assert "MACD Bear Cross" not in trace_names

    def test_custom_params(self):
        macd = MACD(fast=8, slow=21, signal=5)
        assert macd.fast == 8
        assert macd.slow == 21
        assert macd.signal_period == 5

    def test_name(self):
        assert MACD().name == "MACD (12,26,9)"
        assert MACD(fast=8, slow=21, signal=5).name == "MACD (8,21,5)"

    def test_panel_is_separate(self):
        assert MACD().panel == "separate"

    def test_plot_returns_figure(self, sample_ohlcv):
        macd = MACD()
        df = macd.calculate(sample_ohlcv)
        fig = make_subplots(rows=2, cols=1)
        result = macd.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)
        assert len(fig.data) >= 3

    def test_does_not_modify_input(self, sample_ohlcv):
        macd = MACD()
        original = sample_ohlcv.copy()
        macd.calculate(sample_ohlcv)
        pd.testing.assert_frame_equal(sample_ohlcv, original)

    def test_no_crash_on_short_data(self, short_ohlcv):
        macd = MACD()
        result = macd.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert "MACD" in result.columns

    def test_flat_prices(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        macd = MACD()
        result = macd.calculate(df)
        assert (result["MACD"] == 0).all()
        assert (result["MACD_hist"] == 0).all()
