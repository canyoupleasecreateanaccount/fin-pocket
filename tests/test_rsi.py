import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.rsi import RSI


class TestRSI:
    def test_adds_rsi_column(self, sample_ohlcv):
        rsi = RSI()
        result = rsi.calculate(sample_ohlcv)
        assert "RSI" in result.columns

    def test_rsi_range(self, sample_ohlcv):
        rsi = RSI()
        result = rsi.calculate(sample_ohlcv)
        valid = result["RSI"].dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_buy_sell_signals(self, sample_ohlcv):
        rsi = RSI()
        result = rsi.calculate(sample_ohlcv)
        assert "rsi_buy_signal" in result.columns
        assert "rsi_sell_signal" in result.columns
        assert result["rsi_buy_signal"].dtype == bool
        assert result["rsi_sell_signal"].dtype == bool

    def test_custom_levels(self, sample_ohlcv):
        rsi = RSI(overbought=80, oversold=20)
        assert rsi.overbought == 80
        assert rsi.oversold == 20

    def test_panel_is_separate(self):
        assert RSI().panel == "separate"

    def test_name_includes_period(self):
        rsi = RSI(period=21)
        assert "21" in rsi.name

    def test_plot_returns_figure(self, sample_ohlcv):
        rsi = RSI()
        result = rsi.calculate(sample_ohlcv)
        fig = make_subplots(rows=2, cols=1)
        fig = rsi.plot(fig, result, row=2)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_does_not_modify_input(self, sample_ohlcv):
        rsi = RSI()
        original_cols = set(sample_ohlcv.columns)
        rsi.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols
