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

    def test_down_direction_sets_swing_correctly(self):
        """Ensure 'down' direction (swing high before swing low) is detected and plotted."""
        n = 200
        np.random.seed(10)
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.empty(n)
        price = 100.0
        for i in range(n):
            if i < 60:
                price += 3.0 + np.random.normal(0, 0.3)
            elif i < 140:
                price -= 2.5 + np.random.normal(0, 0.3)
            else:
                price += np.random.normal(0, 0.3)
            closes[i] = price
        highs = closes + np.abs(np.random.normal(1, 0.5, n))
        lows = closes - np.abs(np.random.normal(1, 0.5, n))
        df = pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes,
             "Volume": np.random.randint(1_000_000, 5_000_000, n)},
            index=dates,
        )
        fib = Fibonacci(min_move_pct=5.0)
        fib.calculate(df)
        assert fib._direction == "down"
        assert fib._swing_high is not None
        assert fib._swing_low is not None
        assert fib._swing_high["price"] > fib._swing_low["price"]
        assert len(fib._levels) == len(FIB_LEVELS)

        fig = make_subplots(rows=1, cols=1)
        fib.plot(fig, df, row=1)
        assert len(fig.data) > 0

    def test_up_direction_sets_swing_correctly(self):
        """Ensure 'up' direction (swing low before swing high) is detected."""
        n = 200
        np.random.seed(20)
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.empty(n)
        price = 200.0
        for i in range(n):
            if i < 60:
                price -= 2.5 + np.random.normal(0, 0.3)
            elif i < 140:
                price += 3.0 + np.random.normal(0, 0.3)
            else:
                price += np.random.normal(0, 0.3)
            closes[i] = price
        highs = closes + np.abs(np.random.normal(1, 0.5, n))
        lows = closes - np.abs(np.random.normal(1, 0.5, n))
        df = pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes,
             "Volume": np.random.randint(1_000_000, 5_000_000, n)},
            index=dates,
        )
        fib = Fibonacci(min_move_pct=5.0)
        fib.calculate(df)
        assert fib._direction == "up"
        assert fib._swing_low is not None
        assert fib._swing_high is not None

    def test_picks_largest_range_pair(self):
        """The new algorithm should pick the pair with the largest price range."""
        n = 200
        np.random.seed(30)
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.empty(n)
        price = 100.0
        for i in range(n):
            if i < 30:
                price += 0.5 + np.random.normal(0, 0.1)
            elif i < 60:
                price -= 0.3 + np.random.normal(0, 0.1)
            elif i < 100:
                price += 3.0 + np.random.normal(0, 0.2)
            elif i < 160:
                price -= 2.0 + np.random.normal(0, 0.2)
            else:
                price += np.random.normal(0, 0.1)
            closes[i] = price
        highs = closes + np.abs(np.random.normal(0.5, 0.2, n))
        lows = closes - np.abs(np.random.normal(0.5, 0.2, n))
        df = pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes,
             "Volume": np.random.randint(1_000_000, 5_000_000, n)},
            index=dates,
        )
        fib = Fibonacci(min_move_pct=5.0)
        fib.calculate(df)
        if fib._levels:
            level_range = fib._levels[0]["price"] - fib._levels[-1]["price"]
            assert level_range > 20

    def test_plot_with_fills_between_levels(self):
        """Ensure fills are added between Fibonacci levels."""
        fib = Fibonacci(min_move_pct=1.0)
        n = 200
        np.random.seed(40)
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = 100 + np.cumsum(np.random.normal(0, 1, n))
        highs = closes + np.abs(np.random.normal(1, 0.5, n))
        lows = closes - np.abs(np.random.normal(1, 0.5, n))
        df = pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes,
             "Volume": np.random.randint(1_000_000, 5_000_000, n)},
            index=dates,
        )
        fib.calculate(df)
        if fib._levels:
            fig = make_subplots(rows=1, cols=1)
            fib.plot(fig, df, row=1)
            fill_traces = [t for t in fig.data if t.fill == "toself"]
            assert len(fill_traces) == len(FIB_LEVELS) - 1
