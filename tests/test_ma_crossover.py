import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.ma_crossover import MACrossover


class TestMACrossover:
    def test_adds_cross_columns(self, sample_ohlcv):
        mac = MACrossover()
        result = mac.calculate(sample_ohlcv)
        assert "golden_cross" in result.columns
        assert "death_cross" in result.columns

    def test_cross_values_are_boolean(self, sample_ohlcv):
        mac = MACrossover()
        result = mac.calculate(sample_ohlcv)
        assert result["golden_cross"].dtype == bool
        assert result["death_cross"].dtype == bool

    def test_golden_death_mutually_exclusive(self, sample_ohlcv):
        mac = MACrossover()
        result = mac.calculate(sample_ohlcv)
        both = result["golden_cross"] & result["death_cross"]
        assert not both.any()

    def test_custom_periods(self, sample_ohlcv):
        mac = MACrossover(short_period=20, long_period=50)
        result = mac.calculate(sample_ohlcv)
        assert "MA_20" in result.columns
        assert "MA_50" in result.columns

    def test_name_includes_periods(self):
        mac = MACrossover(short_period=10, long_period=30)
        assert "10" in mac.name and "30" in mac.name

    def test_plot_returns_figure(self, sample_ohlcv):
        mac = MACrossover()
        result = mac.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = mac.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)

    def test_does_not_modify_input(self, sample_ohlcv):
        mac = MACrossover()
        original_cols = set(sample_ohlcv.columns)
        mac.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols
