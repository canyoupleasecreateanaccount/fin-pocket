"""Tests for ATR signal."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.atr import ATR


class TestATR:
    def test_calculate_adds_columns(self, sample_ohlcv):
        atr = ATR()
        result = atr.calculate(sample_ohlcv)
        assert "TR" in result.columns
        assert "ATR" in result.columns

    def test_atr_positive(self, sample_ohlcv):
        atr = ATR()
        result = atr.calculate(sample_ohlcv)
        assert (result["ATR"].dropna() >= 0).all()

    def test_custom_period(self):
        atr = ATR(period=7)
        assert atr.period == 7

    def test_name(self):
        atr = ATR()
        assert atr.name == "ATR (14)"
        assert ATR(period=7).name == "ATR (7)"

    def test_panel_is_separate(self):
        atr = ATR()
        assert atr.panel == "separate"

    def test_plot_returns_figure(self, sample_ohlcv):
        atr = ATR()
        df = atr.calculate(sample_ohlcv)
        fig = make_subplots(rows=2, cols=1)
        result = atr.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)
        assert len(fig.data) >= 1

    def test_does_not_modify_input(self, sample_ohlcv):
        atr = ATR()
        original = sample_ohlcv.copy()
        atr.calculate(sample_ohlcv)
        pd.testing.assert_frame_equal(sample_ohlcv, original)

    def test_no_crash_on_short_data(self, short_ohlcv):
        atr = ATR()
        result = atr.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert "ATR" in result.columns

    def test_flat_prices(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        atr = ATR()
        result = atr.calculate(df)
        assert (result["ATR"] == 0).all()
