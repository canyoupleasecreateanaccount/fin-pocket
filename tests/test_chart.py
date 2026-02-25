"""Tests for the Chart builder."""

import plotly.graph_objects as go

from fin_pocket.chart import Chart
from fin_pocket.signals.moving_averages import MovingAverages
from fin_pocket.signals.rsi import RSI


class TestChart:
    def test_build_returns_figure(self, sample_ohlcv):
        chart = Chart(sample_ohlcv, ticker="TEST")
        fig = chart.build()
        assert isinstance(fig, go.Figure)

    def test_build_with_display_days(self, sample_ohlcv):
        chart = Chart(sample_ohlcv, display_days=50)
        fig = chart.build()
        assert isinstance(fig, go.Figure)

    def test_add_signal_returns_self(self, sample_ohlcv):
        chart = Chart(sample_ohlcv)
        result = chart.add_signal(MovingAverages())
        assert result is chart

    def test_build_with_main_signal(self, sample_ohlcv):
        chart = Chart(sample_ohlcv)
        chart.add_signal(MovingAverages(periods=[20]))
        fig = chart.build()
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # candlestick + MA + volume

    def test_build_with_separate_signal(self, sample_ohlcv):
        chart = Chart(sample_ohlcv)
        chart.add_signal(RSI())
        fig = chart.build()
        assert isinstance(fig, go.Figure)

    def test_build_with_multiple_signals(self, sample_ohlcv):
        chart = Chart(sample_ohlcv)
        chart.add_signal(MovingAverages(periods=[20]))
        chart.add_signal(RSI())
        fig = chart.build()
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 3

    def test_custom_height(self, sample_ohlcv):
        chart = Chart(sample_ohlcv, height=800)
        fig = chart.build()
        assert fig.layout.height == 800

    def test_title_with_ticker(self, sample_ohlcv):
        chart = Chart(sample_ohlcv, ticker="AAPL (daily)")
        fig = chart.build()
        assert "AAPL" in fig.layout.title.text
