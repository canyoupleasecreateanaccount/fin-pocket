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
