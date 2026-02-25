import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.wedge import Wedge


class TestWedge:
    def test_calculate_returns_dataframe(self, sample_ohlcv):
        w = Wedge()
        result = w.calculate(sample_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_ohlcv)

    def test_wedges_list_populated(self, sample_ohlcv):
        w = Wedge()
        w.calculate(sample_ohlcv)
        assert isinstance(w._wedges, list)

    def test_wedge_has_required_keys(self, sample_ohlcv):
        w = Wedge()
        w.calculate(sample_ohlcv)
        for wedge in w._wedges:
            assert "type" in wedge
            assert wedge["type"] in ("rising", "falling")
            assert "h1" in wedge
            assert "l1" in wedge
            assert "conv" in wedge

    def test_custom_params(self, sample_ohlcv):
        w = Wedge(lookback=4, min_span=15, max_span=60)
        result = w.calculate(sample_ohlcv)
        assert isinstance(result, pd.DataFrame)

    def test_name(self):
        assert Wedge().name == "Wedge"

    def test_plot_returns_figure(self, sample_ohlcv):
        w = Wedge()
        result = w.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = w.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)

    def test_does_not_modify_input(self, sample_ohlcv):
        w = Wedge()
        original_cols = set(sample_ohlcv.columns)
        w.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols

    def test_no_crash_on_short_data(self, short_ohlcv):
        w = Wedge()
        result = w.calculate(short_ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert len(w._wedges) == 0
