"""Tests for signal plot() methods and uncovered branches.

Covers plot paths that existing tests don't exercise:
- RSI buy/sell markers on plot
- MA Crossover golden/death markers on plot  
- RSI Divergence bullish/bearish lines on plot
- Volume Breakout buy/sell markers on plot
- Support/Resistance rendering with both supports and resistances
- Wedge breakout vs no-breakout plot paths
- Fibonacci swing marker visibility
- Pennant bear flag/pennant plot paths
- Double Top/Bottom confirmation markers, overlapping zones, visibility filter
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.rsi import RSI
from fin_pocket.signals.rsi_divergence import RSIDivergence
from fin_pocket.signals.ma_crossover import MACrossover
from fin_pocket.signals.moving_averages import MovingAverages
from fin_pocket.signals.volume_breakout import VolumeBreakout
from fin_pocket.signals.support_resistance import SupportResistance
from fin_pocket.signals.wedge import Wedge
from fin_pocket.signals.fibonacci import Fibonacci
from fin_pocket.signals.pennant import Pennant
from fin_pocket.signals.double_top_bottom import DoubleTopBottom


def _make_fig(rows=2):
    return make_subplots(rows=rows, cols=1)


def _sample(n=200, seed=42):
    np.random.seed(seed)
    dates = pd.bdate_range("2024-01-02", periods=n)
    closes = 100 + np.cumsum(np.random.normal(0, 1, n))
    highs = closes + np.abs(np.random.normal(0.5, 0.3, n))
    lows = closes - np.abs(np.random.normal(0.5, 0.3, n))
    opens = lows + (highs - lows) * 0.5
    volumes = np.random.randint(1_000_000, 5_000_000, n)
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=dates,
    )


# ---------- RSI plot with buy/sell signals ----------

class TestRSIPlotSignals:
    def test_plot_with_buy_sell_markers(self):
        df = _sample()
        rsi = RSI(period=14, overbought=60, oversold=40)
        df = rsi.calculate(df)
        fig = _make_fig()
        result = rsi.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)
        assert len(fig.data) >= 1

    def test_plot_no_buy_sell_signals(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.linspace(100, 110, n)
        highs = closes + 0.5
        lows = closes - 0.5
        df = pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes,
             "Volume": [1_000_000] * n},
            index=dates,
        )
        rsi = RSI()
        df = rsi.calculate(df)
        fig = _make_fig()
        rsi.plot(fig, df, row=1)
        assert isinstance(fig, go.Figure)


# ---------- MA Crossover plot ----------

class TestMACrossoverPlot:
    def test_plot_with_crosses(self):
        n = 300
        np.random.seed(10)
        dates = pd.bdate_range("2023-01-02", periods=n)
        closes = []
        price = 100.0
        for i in range(n):
            if i < 150:
                price *= 1 + np.random.normal(0.003, 0.01)
            else:
                price *= 1 + np.random.normal(-0.003, 0.01)
            closes.append(price)
        closes = np.array(closes)
        highs = closes + 1
        lows = closes - 1
        df = pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes,
             "Volume": [1_000_000] * n},
            index=dates,
        )
        mac = MACrossover()
        df = mac.calculate(df)
        fig = _make_fig()
        result = mac.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)

    def test_plot_no_crosses(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.linspace(100, 110, n)
        df = pd.DataFrame(
            {"Open": closes, "High": closes + 0.5, "Low": closes - 0.5,
             "Close": closes, "Volume": [1_000_000] * n},
            index=dates,
        )
        mac = MACrossover()
        df = mac.calculate(df)
        fig = _make_fig()
        mac.plot(fig, df, row=1)


# ---------- RSI Divergence plot ----------

class TestRSIDivergencePlot:
    def _make_divergence_data(self):
        n = 200
        np.random.seed(5)
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = []
        price = 100.0
        for i in range(n):
            if i < 50:
                price *= 1 + np.random.normal(-0.005, 0.01)
            elif i < 100:
                price *= 1 + np.random.normal(0.003, 0.01)
            elif i < 150:
                price *= 1 + np.random.normal(-0.006, 0.01)
            else:
                price *= 1 + np.random.normal(0.004, 0.01)
            closes.append(price)
        closes = np.array(closes)
        highs = closes + np.abs(np.random.normal(0.5, 0.3, n))
        lows = closes - np.abs(np.random.normal(0.5, 0.3, n))
        return pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes,
             "Volume": np.random.randint(1_000_000, 5_000_000, n)},
            index=dates,
        )

    def test_plot_with_divergences(self):
        df = self._make_divergence_data()
        div = RSIDivergence()
        df = div.calculate(df)
        fig = _make_fig()
        result = div.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)

    def test_plot_no_divergences(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.linspace(100, 110, n)
        df = pd.DataFrame(
            {"Open": closes, "High": closes + 0.5, "Low": closes - 0.5,
             "Close": closes, "Volume": [1_000_000] * n},
            index=dates,
        )
        div = RSIDivergence()
        df = div.calculate(df)
        fig = _make_fig()
        div.plot(fig, df, row=1)


# ---------- Volume Breakout plot ----------

class TestVolumeBreakoutPlot:
    def test_plot_with_signals(self, sample_ohlcv):
        sr = SupportResistance()
        df = sr.calculate(sample_ohlcv)
        vb = VolumeBreakout()
        df = vb.calculate(df)
        fig = _make_fig()
        result = vb.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)

    def test_plot_no_signals(self):
        n = 30
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [100]*n},
            index=dates,
        )
        df["vol_breakout_buy"] = False
        df["vol_breakout_sell"] = False
        df["vol_ratio"] = 0.0
        vb = VolumeBreakout()
        fig = _make_fig()
        vb.plot(fig, df, row=1)


# ---------- Support/Resistance plot ----------

class TestSupportResistancePlot:
    def test_plot_with_levels(self, sample_ohlcv):
        sr = SupportResistance()
        df = sr.calculate(sample_ohlcv)
        fig = _make_fig()
        result = sr.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)

    def test_plot_no_levels(self):
        n = 5
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        df.attrs["support_resistance_levels"] = []
        sr = SupportResistance()
        fig = _make_fig()
        sr.plot(fig, df, row=1)


# ---------- Wedge plot ----------

class TestWedgePlot:
    def test_plot_empty_wedges(self, sample_ohlcv):
        w = Wedge()
        w._wedges = []
        fig = _make_fig()
        result = w.plot(fig, sample_ohlcv, row=1)
        assert len(fig.data) == 0

    def test_plot_not_visible(self, sample_ohlcv):
        w = Wedge()
        w._wedges = [{
            "h1": {"date": pd.Timestamp("2020-01-01"), "val": 100, "idx": 0},
            "h2": {"date": pd.Timestamp("2020-06-01"), "val": 110, "idx": 50},
            "l1": {"date": pd.Timestamp("2020-01-01"), "val": 90, "idx": 0},
            "type": "rising",
            "h_slope": 0.1, "h_int": 100, "l_slope": 0.15, "l_int": 90,
            "draw_end": 60, "draw_end_date": pd.Timestamp("2020-07-01"),
            "breakout": False, "h_touches": [], "l_touches": [],
            "score": 1, "conv": 0.3,
        }]
        fig = _make_fig()
        w.plot(fig, sample_ohlcv, row=1)


# ---------- Fibonacci plot ----------

class TestFibonacciPlot:
    def test_plot_with_levels(self, sample_ohlcv):
        fib = Fibonacci()
        df = fib.calculate(sample_ohlcv)
        fig = _make_fig()
        result = fib.plot(fig, df, row=1)
        assert isinstance(result, go.Figure)

    def test_plot_no_levels(self):
        n = 5
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        fib = Fibonacci()
        fib._levels = []
        fig = _make_fig()
        fib.plot(fig, df, row=1)


# ---------- Pennant plot ----------

class TestPennantPlot:
    def test_plot_empty_patterns(self, sample_ohlcv):
        p = Pennant()
        p._patterns = []
        fig = _make_fig()
        result = p.plot(fig, sample_ohlcv, row=1)
        assert len(fig.data) == 0

    def test_plot_not_visible(self, sample_ohlcv):
        p = Pennant()
        p._patterns = [{
            "type": "bull", "form": "flag",
            "pole_start_date": pd.Timestamp("2020-01-01"),
            "pole_end_date": pd.Timestamp("2020-01-10"),
            "body_start_date": pd.Timestamp("2020-01-10"),
            "body_end_date": pd.Timestamp("2020-02-01"),
            "pole_start_price": 100, "pole_end_price": 120,
            "pole_move_pct": 20.0,
            "body": {"h_start_val": 120, "h_end_val": 118,
                     "l_start_val": 115, "l_end_val": 113,
                     "retrace": 0.2, "width_ratio": 0.8},
            "score": 10,
        }]
        fig = _make_fig()
        p.plot(fig, sample_ohlcv, row=1)


# ---------- Double Top/Bottom plot ----------

class TestDoubleTopBottomPlot:
    def test_plot_empty_patterns(self, sample_ohlcv):
        dtb = DoubleTopBottom()
        dtb._patterns = []
        fig = _make_fig()
        result = dtb.plot(fig, sample_ohlcv, row=1)
        assert len(fig.data) == 0

    def test_plot_with_confirmed_double_top(self, sample_ohlcv):
        dates = sample_ohlcv.index
        dtb = DoubleTopBottom()
        dtb._patterns = [{
            "type": "double_top",
            "idx1": 50, "val1": 110.0,
            "idx2": 100, "val2": 109.5,
            "neckline": 95.0,
            "depth_pct": 13.0,
            "confirmed": True,
            "confirm_idx": 120,
            "date1": dates[50],
            "date2": dates[100],
            "confirm_date": dates[120],
            "score": 26.0,
        }]
        fig = _make_fig()
        result = dtb.plot(fig, sample_ohlcv, row=1)
        assert len(fig.data) >= 2

    def test_plot_with_unconfirmed_double_bottom(self, sample_ohlcv):
        dates = sample_ohlcv.index
        dtb = DoubleTopBottom()
        dtb._patterns = [{
            "type": "double_bottom",
            "idx1": 30, "val1": 90.0,
            "idx2": 80, "val2": 91.0,
            "neckline": 105.0,
            "depth_pct": 15.0,
            "confirmed": False,
            "confirm_idx": None,
            "date1": dates[30],
            "date2": dates[80],
            "confirm_date": None,
            "score": 15.0,
        }]
        fig = _make_fig()
        result = dtb.plot(fig, sample_ohlcv, row=1)
        assert len(fig.data) >= 2

    def test_plot_not_visible(self, sample_ohlcv):
        dtb = DoubleTopBottom()
        dtb._patterns = [{
            "type": "double_top",
            "idx1": 0, "val1": 100.0,
            "idx2": 10, "val2": 100.5,
            "neckline": 90.0, "depth_pct": 10.0,
            "confirmed": False, "confirm_idx": None,
            "date1": pd.Timestamp("2020-01-01"),
            "date2": pd.Timestamp("2020-02-01"),
            "confirm_date": None,
            "score": 10.0,
        }]
        fig = _make_fig()
        dtb.plot(fig, sample_ohlcv, row=1)
        assert len(fig.data) == 0


# ---------- Moving Averages plot edge cases ----------

class TestMovingAveragesPlot:
    def test_plot_missing_column(self):
        n = 30
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {"Open": [100.0]*n, "High": [100.0]*n, "Low": [100.0]*n,
             "Close": [100.0]*n, "Volume": [1_000_000]*n},
            index=dates,
        )
        ma = MovingAverages(periods=[50, 100])
        fig = _make_fig()
        ma.plot(fig, df, row=1)
        assert len(fig.data) == 0

    def test_plot_custom_period_color(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.linspace(100, 110, n)
        df = pd.DataFrame(
            {"Open": closes, "High": closes + 0.5, "Low": closes - 0.5,
             "Close": closes, "Volume": [1_000_000] * n},
            index=dates,
        )
        ma = MovingAverages(periods=[10])
        df = ma.calculate(df)
        fig = _make_fig()
        ma.plot(fig, df, row=1)
        assert len(fig.data) == 1


# ---------- MACrossover calculate with existing MA columns ----------

class TestMACrossoverExistingColumns:
    def test_uses_existing_ma_columns(self):
        n = 250
        dates = pd.bdate_range("2023-01-02", periods=n)
        closes = 100 + np.cumsum(np.random.normal(0, 1, n))
        df = pd.DataFrame(
            {"Open": closes, "High": closes + 0.5, "Low": closes - 0.5,
             "Close": closes, "Volume": [1_000_000] * n},
            index=dates,
        )
        df["MA_50"] = df["Close"].rolling(50).mean()
        df["MA_200"] = df["Close"].rolling(200).mean()
        mac = MACrossover()
        result = mac.calculate(df)
        assert "golden_cross" in result.columns
        assert "death_cross" in result.columns


# ---------- SupportResistance cluster edge cases ----------

class TestSupportResistanceEdges:
    def test_cluster_zero_level(self):
        sr = SupportResistance()
        result = sr._cluster_levels([0.0, 0.0], 100.0)
        assert isinstance(result, list)

    def test_cluster_empty(self):
        sr = SupportResistance()
        result = sr._cluster_levels([], 100.0)
        assert result == []


# ---------- RSIDivergence calculate with existing RSI ----------

class TestRSIDivergenceExistingRSI:
    def test_uses_existing_rsi_column(self):
        n = 100
        dates = pd.bdate_range("2024-01-02", periods=n)
        np.random.seed(42)
        closes = 100 + np.cumsum(np.random.normal(0, 1, n))
        df = pd.DataFrame(
            {"Open": closes, "High": closes + 0.5, "Low": closes - 0.5,
             "Close": closes, "Volume": [1_000_000] * n},
            index=dates,
        )
        df["RSI"] = 50.0
        div = RSIDivergence()
        result = div.calculate(df)
        assert "bullish_divergence" in result.columns
