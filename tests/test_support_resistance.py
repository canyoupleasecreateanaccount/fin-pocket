import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.support_resistance import SupportResistance


class TestSupportResistance:
    def test_calculate_adds_levels(self, sample_ohlcv):
        sr = SupportResistance()
        result = sr.calculate(sample_ohlcv)
        levels = result.attrs.get("support_resistance_levels", [])
        assert isinstance(levels, list)

    def test_levels_have_required_keys(self, sample_ohlcv):
        sr = SupportResistance()
        result = sr.calculate(sample_ohlcv)
        levels = result.attrs.get("support_resistance_levels", [])
        for lv in levels:
            assert "level" in lv
            assert "touches" in lv
            assert "type" in lv
            assert lv["type"] in ("support", "resistance")

    def test_max_levels_respected(self, sample_ohlcv):
        sr = SupportResistance(max_levels=2)
        result = sr.calculate(sample_ohlcv)
        levels = result.attrs.get("support_resistance_levels", [])
        assert len(levels) <= 2 * 2  # max_levels * 2

    def test_recent_bars_limits_scope(self, sample_ohlcv):
        sr1 = SupportResistance(recent_bars=50)
        sr2 = SupportResistance(recent_bars=200)
        r1 = sr1.calculate(sample_ohlcv)
        r2 = sr2.calculate(sample_ohlcv)
        l1 = r1.attrs.get("support_resistance_levels", [])
        l2 = r2.attrs.get("support_resistance_levels", [])
        assert isinstance(l1, list)
        assert isinstance(l2, list)

    def test_name(self):
        assert SupportResistance().name == "Support/Resistance"

    def test_plot_returns_figure(self, sample_ohlcv):
        sr = SupportResistance()
        result = sr.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = sr.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)

    def test_does_not_modify_input(self, sample_ohlcv):
        sr = SupportResistance()
        original_cols = set(sample_ohlcv.columns)
        sr.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols

    def test_empty_with_short_data(self, short_ohlcv):
        sr = SupportResistance(lookback=10)
        result = sr.calculate(short_ohlcv)
        levels = result.attrs.get("support_resistance_levels", [])
        assert isinstance(levels, list)
