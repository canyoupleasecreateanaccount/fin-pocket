"""Tests for Bollinger Bands signal."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.bollinger_bands import BollingerBands


class TestBollingerBands:
    def test_calculate_adds_columns(self, sample_ohlcv):
        bb = BollingerBands()
        result = bb.calculate(sample_ohlcv)
        assert "BB_upper" in result.columns
        assert "BB_middle" in result.columns
        assert "BB_lower" in result.columns

    def test_upper_above_lower(self, sample_ohlcv):
        bb = BollingerBands()
        result = bb.calculate(sample_ohlcv)
        valid = result.dropna(subset=["BB_upper", "BB_lower"])
        assert (valid["BB_upper"] >= valid["BB_lower"]).all()

    def test_middle_between_bands(self, sample_ohlcv):
        bb = BollingerBands()
        result = bb.calculate(sample_ohlcv)
        valid = result.dropna(subset=["BB_upper", "BB_middle", "BB_lower"])
        assert (valid["BB_middle"] >= valid["BB_lower"]).all()
        assert (valid["BB_middle"] <= valid["BB_upper"]).all()

    def test_custom_params(self):
        bb = BollingerBands(period=10, std_dev=1.5)
        assert bb.period == 10
        assert bb.std_dev == 1.5

    def test_name(self):
        assert BollingerBands().name == "BB (20,2.0)"
        assert BollingerBands(period=10, std_dev=1.5).name == "BB (10,1.5)"

    def test_panel_is_main(self):
        assert BollingerBands().panel == "main"

    def test_plot_returns_figure(self, sample_ohlcv):
        bb = BollingerBands()
        df = bb.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        result = bb.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)
        assert len(fig.data) == 3

    def test_does_not_modify_input(self, sample_ohlcv):
        bb = BollingerBands()
        original = sample_ohlcv.copy()
        bb.calculate(sample_ohlcv)
        pd.testing.assert_frame_equal(sample_ohlcv, original)

    def test_no_crash_on_short_data(self, short_ohlcv):
        bb = BollingerBands()
        result = bb.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert "BB_upper" in result.columns

    def test_flat_prices(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        bb = BollingerBands()
        result = bb.calculate(df)
        assert (result["BB_upper"] == 100.0).all()
        assert (result["BB_lower"] == 100.0).all()
