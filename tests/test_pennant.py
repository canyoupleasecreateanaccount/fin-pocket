import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.pennant import Pennant


class TestPennant:
    def test_calculate_returns_dataframe(self, sample_ohlcv):
        p = Pennant()
        result = p.calculate(sample_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_ohlcv)

    def test_patterns_list_populated(self, sample_ohlcv):
        p = Pennant()
        p.calculate(sample_ohlcv)
        assert isinstance(p._patterns, list)

    def test_pattern_has_required_keys(self, sample_ohlcv):
        p = Pennant()
        p.calculate(sample_ohlcv)
        for pat in p._patterns:
            assert "type" in pat
            assert pat["type"] in ("bull", "bear")
            assert "form" in pat
            assert pat["form"] in ("flag", "pennant")
            assert "pole_start_date" in pat
            assert "body_end_date" in pat
            assert "body" in pat
            assert "score" in pat

    def test_custom_params(self, sample_ohlcv):
        p = Pennant(lookback=3, min_pole_bars=3, max_pole_bars=10, min_pole_move_pct=3.0)
        result = p.calculate(sample_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_name(self):
        assert Pennant().name == "Flag & Pennant"

    def test_plot_returns_figure(self, sample_ohlcv):
        p = Pennant()
        result = p.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = p.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)

    def test_does_not_modify_input(self, sample_ohlcv):
        p = Pennant()
        original_cols = set(sample_ohlcv.columns)
        p.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols

    def test_no_crash_on_short_data(self, short_ohlcv):
        p = Pennant()
        result = p.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert len(p._patterns) == 0

    def test_bull_flag_on_trending_data(self, trending_up_ohlcv):
        p = Pennant(min_pole_move_pct=3.0)
        p.calculate(trending_up_ohlcv)
        bull_patterns = [pat for pat in p._patterns if pat["type"] == "bull"]
        assert isinstance(bull_patterns, list)
