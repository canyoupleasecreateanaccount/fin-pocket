import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.rsi_divergence import RSIDivergence


class TestRSIDivergence:
    def test_adds_columns(self, sample_ohlcv):
        rd = RSIDivergence()
        result = rd.calculate(sample_ohlcv)
        assert "bullish_divergence" in result.columns
        assert "bearish_divergence" in result.columns
        assert "RSI" in result.columns

    def test_divergence_types_are_boolean(self, sample_ohlcv):
        rd = RSIDivergence()
        result = rd.calculate(sample_ohlcv)
        assert result["bullish_divergence"].dtype == bool
        assert result["bearish_divergence"].dtype == bool

    def test_name(self):
        assert RSIDivergence().name == "RSI Divergence"

    def test_plot_returns_figure(self, sample_ohlcv):
        rd = RSIDivergence()
        result = rd.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = rd.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)

    def test_does_not_modify_input(self, sample_ohlcv):
        rd = RSIDivergence()
        original_cols = set(sample_ohlcv.columns)
        rd.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols
