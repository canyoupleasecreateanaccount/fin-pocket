import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.moving_averages import MovingAverages


class TestMovingAverages:
    def test_default_periods(self, sample_ohlcv):
        ma = MovingAverages()
        assert ma.periods == [50, 100, 200]

    def test_custom_periods(self, sample_ohlcv):
        ma = MovingAverages(periods=[20, 50])
        result = ma.calculate(sample_ohlcv)
        assert "MA_20" in result.columns
        assert "MA_50" in result.columns
        assert "MA_200" not in result.columns

    def test_calculate_adds_columns(self, sample_ohlcv):
        ma = MovingAverages()
        result = ma.calculate(sample_ohlcv)
        for period in [50, 100, 200]:
            assert f"MA_{period}" in result.columns

    def test_ma_values_are_averages(self, sample_ohlcv):
        ma = MovingAverages(periods=[50])
        result = ma.calculate(sample_ohlcv)
        expected = sample_ohlcv["Close"].rolling(50).mean()
        pd.testing.assert_series_equal(result["MA_50"], expected, check_names=False)

    def test_ma_has_nans_at_start(self, sample_ohlcv):
        ma = MovingAverages(periods=[50])
        result = ma.calculate(sample_ohlcv)
        assert result["MA_50"].iloc[:49].isna().all()
        assert result["MA_50"].iloc[49:].notna().all()

    def test_name(self):
        assert MovingAverages().name == "Moving Averages"

    def test_panel_is_main(self):
        assert MovingAverages().panel == "main"

    def test_plot_returns_figure(self, sample_ohlcv):
        ma = MovingAverages(periods=[50])
        result = ma.calculate(sample_ohlcv)
        fig = make_subplots(rows=1, cols=1)
        fig = ma.plot(fig, result, row=1)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_does_not_modify_input(self, sample_ohlcv):
        ma = MovingAverages()
        original_cols = set(sample_ohlcv.columns)
        ma.calculate(sample_ohlcv)
        assert set(sample_ohlcv.columns) == original_cols
