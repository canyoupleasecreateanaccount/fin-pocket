"""Tests for OBV signal."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.obv import OBV


class TestOBV:
    def test_calculate_adds_columns(self, sample_ohlcv):
        obv = OBV()
        result = obv.calculate(sample_ohlcv)
        assert "OBV" in result.columns
        assert "OBV_MA" in result.columns

    def test_obv_direction(self):
        dates = pd.bdate_range("2024-01-02", periods=5)
        df = pd.DataFrame(
            {"Open": [100, 101, 102, 101, 100],
             "High": [101, 102, 103, 102, 101],
             "Low": [99, 100, 101, 100, 99],
             "Close": [100, 102, 101, 103, 100],
             "Volume": [1000, 2000, 3000, 4000, 5000]},
            index=dates,
        )
        obv = OBV()
        result = obv.calculate(df)
        assert result["OBV"].iloc[1] == 2000
        assert result["OBV"].iloc[2] == 2000 - 3000

    def test_custom_ma_period(self):
        obv = OBV(ma_period=10)
        assert obv.ma_period == 10

    def test_name(self):
        assert OBV().name == "OBV"

    def test_panel_is_separate(self):
        assert OBV().panel == "separate"

    def test_plot_returns_figure(self, sample_ohlcv):
        obv = OBV()
        df = obv.calculate(sample_ohlcv)
        fig = make_subplots(rows=2, cols=1)
        result = obv.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)
        assert len(fig.data) >= 2

    def test_does_not_modify_input(self, sample_ohlcv):
        obv = OBV()
        original = sample_ohlcv.copy()
        obv.calculate(sample_ohlcv)
        pd.testing.assert_frame_equal(sample_ohlcv, original)

    def test_no_crash_on_short_data(self, short_ohlcv):
        obv = OBV()
        result = obv.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert "OBV" in result.columns

    def test_flat_prices_obv_zero(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        obv = OBV()
        result = obv.calculate(df)
        assert (result["OBV"] == 0).all()


class TestOBVFormat:
    def test_fmt_billions(self):
        assert OBV._fmt(2_500_000_000) == "2.50B"

    def test_fmt_negative_billions(self):
        assert OBV._fmt(-1_200_000_000) == "-1.20B"

    def test_fmt_millions(self):
        assert OBV._fmt(25_867_830) == "25.87M"

    def test_fmt_negative_millions(self):
        assert OBV._fmt(-3_450_000) == "-3.45M"

    def test_fmt_thousands(self):
        assert OBV._fmt(7_500) == "7.5K"

    def test_fmt_negative_thousands(self):
        assert OBV._fmt(-1_234) == "-1.2K"

    def test_fmt_small_number(self):
        assert OBV._fmt(42) == "42"

    def test_fmt_zero(self):
        assert OBV._fmt(0) == "0"

    def test_fmt_negative_small(self):
        assert OBV._fmt(-99) == "-99"

    def test_plot_obv_above_ma(self):
        """OBV > MA: OBV label shifted up, MA label shifted down."""
        dates = pd.bdate_range("2024-01-02", periods=10)
        closes = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
        df = pd.DataFrame(
            {"Open": closes, "High": [c + 1 for c in closes],
             "Low": [c - 1 for c in closes], "Close": closes,
             "Volume": [1_000_000] * 10},
            index=dates,
        )
        obv = OBV()
        df = obv.calculate(df)
        fig = make_subplots(rows=2, cols=1)
        obv.plot(fig, df, row=1)
        annotations = [a for a in fig.layout.annotations if "OBV" in a.text or "MA" in a.text]
        assert len(annotations) == 2

    def test_plot_obv_below_ma(self):
        """OBV < MA: MA label shifted up, OBV label shifted down."""
        dates = pd.bdate_range("2024-01-02", periods=10)
        closes = [118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
        df = pd.DataFrame(
            {"Open": closes, "High": [c + 1 for c in closes],
             "Low": [c - 1 for c in closes], "Close": closes,
             "Volume": [1_000_000] * 10},
            index=dates,
        )
        obv = OBV()
        df = obv.calculate(df)
        fig = make_subplots(rows=2, cols=1)
        obv.plot(fig, df, row=1)
        annotations = [a for a in fig.layout.annotations if "OBV" in a.text or "MA" in a.text]
        assert len(annotations) == 2
