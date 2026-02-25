import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.fibonacci import Fibonacci, FIB_LEVELS


class TestFibonacci:
    def test_calculate_returns_dataframe(self, sample_ohlcv):
        fib = Fibonacci()
        result = fib.calculate(sample_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_ohlcv)

    def test_levels_populated(self, sample_ohlcv):
        fib = Fibonacci()
        fib.calculate(sample_ohlcv)
        assert isinstance(fib._levels, list)

    def test_level_has_required_keys(self, sample_ohlcv):
        fib = Fibonacci()
        fib.calculate(sample_ohlcv)
        for lv in fib._levels:
            assert "fib" in lv
            assert "price" in lv
            assert lv["fib"] in FIB_LEVELS

    def test_seven_levels_when_found(self, sample_ohlcv):
        fib = Fibonacci(min_move_pct=1.0)
        fib.calculate(sample_ohlcv)
        if fib._levels:
            assert len(fib._levels) == len(FIB_LEVELS)

    def test_levels_ordered_descending(self, sample_ohlcv):
        fib = Fibonacci(min_move_pct=1.0)
        fib.calculate(sample_ohlcv)
        if fib._levels:
            prices = [lv["price"] for lv in fib._levels]
            assert prices == sorted(prices, reverse=True)

    def test_custom_params(self, sample_ohlcv):
        fib = Fibonacci(lookback=5, min_move_pct=3.0, recent_bars=100)
        result = fib.calculate(sample_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_name(self):
        assert Fibonacci().name == "Fibonacci"

    def test_plot_returns_figure(self, sample_ohlcv):
        fib = Fibonacci()
        result = fib.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = fib.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)

    def test_does_not_modify_input(self, sample_ohlcv):
        fib = Fibonacci()
        original_cols = set(sample_ohlcv.columns)
        fib.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols

    def test_no_crash_on_short_data(self, short_ohlcv):
        fib = Fibonacci()
        result = fib.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)
