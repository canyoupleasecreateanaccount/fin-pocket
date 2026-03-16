import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.volume_breakout import VolumeBreakout


class TestVolumeBreakout:
    def test_adds_columns(self, sample_ohlcv):
        vb = VolumeBreakout()
        result = vb.calculate(sample_ohlcv)
        assert "vol_breakout_buy" in result.columns
        assert "vol_breakout_sell" in result.columns
        assert "vol_ratio" in result.columns

    def test_signal_types_are_boolean(self, sample_ohlcv):
        vb = VolumeBreakout()
        result = vb.calculate(sample_ohlcv)
        assert result["vol_breakout_buy"].dtype == bool
        assert result["vol_breakout_sell"].dtype == bool

    def test_vol_ratio_positive(self, sample_ohlcv):
        vb = VolumeBreakout()
        result = vb.calculate(sample_ohlcv)
        valid = result["vol_ratio"].dropna()
        assert (valid > 0).all()

    def test_custom_params(self, sample_ohlcv):
        vb = VolumeBreakout(vol_period=20, vol_threshold=2.0)
        result = vb.calculate(sample_ohlcv)
        assert "vol_breakout_buy" in result.columns

    def test_name(self):
        assert VolumeBreakout().name == "Volume Breakout"

    def test_plot_returns_figure(self, sample_ohlcv):
        vb = VolumeBreakout()
        result = vb.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = vb.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)

    def test_does_not_modify_input(self, sample_ohlcv):
        vb = VolumeBreakout()
        original_cols = set(sample_ohlcv.columns)
        vb.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols

    def test_buy_signal_plotted(self):
        """Ensure buy signal markers appear when vol_breakout_buy is True."""
        import numpy as np
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        closes = np.linspace(100, 120, n)
        df = pd.DataFrame(
            {"Open": closes, "High": closes + 1, "Low": closes - 1,
             "Close": closes, "Volume": [1_000_000] * n},
            index=dates,
        )
        df["vol_breakout_buy"] = False
        df["vol_breakout_sell"] = False
        df["vol_ratio"] = 1.5
        df.loc[df.index[20], "vol_breakout_buy"] = True
        from plotly.subplots import make_subplots
        vb = VolumeBreakout()
        fig = make_subplots(rows=1, cols=1)
        vb.plot(fig, df, row=1)
        trace_names = [t.name for t in fig.data]
        assert "Vol Breakout ↑" in trace_names
