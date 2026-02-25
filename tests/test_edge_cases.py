"""Edge case tests: empty data, flat prices, division by zero scenarios."""

import numpy as np
import pandas as pd
import pytest
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.chart import Chart
from fin_pocket.signals.rsi import RSI
from fin_pocket.signals.rsi_divergence import RSIDivergence
from fin_pocket.signals.moving_averages import MovingAverages
from fin_pocket.signals.ma_crossover import MACrossover
from fin_pocket.signals.support_resistance import SupportResistance
from fin_pocket.signals.volume_breakout import VolumeBreakout
from fin_pocket.signals.wedge import Wedge
from fin_pocket.signals.pennant import Pennant
from fin_pocket.signals.fibonacci import Fibonacci


@pytest.fixture
def empty_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["Open", "High", "Low", "Close", "Volume"],
        dtype=float,
    )


@pytest.fixture
def single_row_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0],
            "High": [105.0],
            "Low": [95.0],
            "Close": [102.0],
            "Volume": [1_000_000],
        },
        index=pd.bdate_range("2024-01-02", periods=1),
    )


@pytest.fixture
def flat_ohlcv() -> pd.DataFrame:
    n = 100
    dates = pd.bdate_range("2024-01-02", periods=n)
    price = 50.0
    return pd.DataFrame(
        {
            "Open": [price] * n,
            "High": [price] * n,
            "Low": [price] * n,
            "Close": [price] * n,
            "Volume": [1_000_000] * n,
        },
        index=dates,
    )


@pytest.fixture
def all_gains_ohlcv() -> pd.DataFrame:
    """Monotonically rising prices — avg_loss is always 0."""
    n = 50
    dates = pd.bdate_range("2024-01-02", periods=n)
    closes = [100.0 + i for i in range(n)]
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c + 1 for c in closes],
            "Low": [c - 0.5 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * n,
        },
        index=dates,
    )


@pytest.fixture
def zero_volume_ohlcv() -> pd.DataFrame:
    n = 100
    np.random.seed(55)
    dates = pd.bdate_range("2024-01-02", periods=n)
    closes = 100.0 + np.cumsum(np.random.normal(0, 1, n))
    return pd.DataFrame(
        {
            "Open": closes - 0.5,
            "High": closes + 1,
            "Low": closes - 1,
            "Close": closes,
            "Volume": [0] * n,
        },
        index=dates,
    )


class TestRSIEdgeCases:
    def test_all_gains_no_crash(self, all_gains_ohlcv):
        rsi = RSI()
        result = rsi.calculate(all_gains_ohlcv)
        assert "RSI" in result.columns
        assert result["RSI"].notna().any()

    def test_flat_prices(self, flat_ohlcv):
        rsi = RSI()
        result = rsi.calculate(flat_ohlcv)
        assert "RSI" in result.columns

    def test_single_row(self, single_row_ohlcv):
        rsi = RSI()
        result = rsi.calculate(single_row_ohlcv)
        assert len(result) == 1


class TestRSIDivergenceEdgeCases:
    def test_all_gains_no_crash(self, all_gains_ohlcv):
        div = RSIDivergence()
        result = div.calculate(all_gains_ohlcv)
        assert "bullish_divergence" in result.columns

    def test_flat_prices(self, flat_ohlcv):
        div = RSIDivergence()
        result = div.calculate(flat_ohlcv)
        assert "bearish_divergence" in result.columns


class TestChartEdgeCases:
    def test_flat_prices_no_crash(self, flat_ohlcv):
        chart = Chart(flat_ohlcv, ticker="FLAT")
        fig = chart.build()
        assert isinstance(fig, go.Figure)

    def test_single_row_no_crash(self, single_row_ohlcv):
        chart = Chart(single_row_ohlcv, ticker="ONE")
        fig = chart.build()
        assert isinstance(fig, go.Figure)

    def test_signal_failure_does_not_crash_chart(self, sample_ohlcv):
        """If a signal raises, the chart still builds."""
        from fin_pocket.signals.base import BaseSignal

        class BrokenSignal(BaseSignal):
            @property
            def name(self):
                return "Broken"

            def calculate(self, data):
                raise RuntimeError("intentional failure")

            def plot(self, fig, data, row=1):
                return fig

        chart = Chart(sample_ohlcv, ticker="TEST")
        chart.add_signal(BrokenSignal())
        fig = chart.build()
        assert isinstance(fig, go.Figure)


class TestVolumeBreakoutEdgeCases:
    def test_zero_volume(self, zero_volume_ohlcv):
        vb = VolumeBreakout()
        result = vb.calculate(zero_volume_ohlcv)
        assert "vol_ratio" in result.columns
        assert not result["vol_ratio"].isna().all()


class TestSupportResistanceEdgeCases:
    def test_flat_prices(self, flat_ohlcv):
        sr = SupportResistance()
        result = sr.calculate(flat_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_single_row(self, single_row_ohlcv):
        sr = SupportResistance()
        result = sr.calculate(single_row_ohlcv)
        assert isinstance(result, pd.DataFrame)


class TestFibonacciEdgeCases:
    def test_flat_prices(self, flat_ohlcv):
        fib = Fibonacci()
        result = fib.calculate(flat_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_single_row(self, single_row_ohlcv):
        fib = Fibonacci()
        result = fib.calculate(single_row_ohlcv)
        assert isinstance(result, pd.DataFrame)


class TestPennantEdgeCases:
    def test_flat_prices(self, flat_ohlcv):
        p = Pennant()
        result = p.calculate(flat_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_single_row(self, single_row_ohlcv):
        p = Pennant()
        result = p.calculate(single_row_ohlcv)
        assert isinstance(result, pd.DataFrame)


class TestWedgeEdgeCases:
    def test_flat_prices(self, flat_ohlcv):
        w = Wedge()
        result = w.calculate(flat_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_single_row(self, single_row_ohlcv):
        w = Wedge()
        result = w.calculate(single_row_ohlcv)
        assert isinstance(result, pd.DataFrame)


class TestMovingAveragesEdgeCases:
    def test_single_row(self, single_row_ohlcv):
        ma = MovingAverages()
        result = ma.calculate(single_row_ohlcv)
        assert isinstance(result, pd.DataFrame)


class TestMACrossoverEdgeCases:
    def test_single_row(self, single_row_ohlcv):
        mac = MACrossover()
        result = mac.calculate(single_row_ohlcv)
        assert isinstance(result, pd.DataFrame)
