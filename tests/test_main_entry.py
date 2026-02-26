"""Tests for __main__.py, __init__.py, cli.main(), chart.show/save."""

from unittest.mock import patch, MagicMock
import importlib

import pandas as pd
import numpy as np
import pytest
import plotly.graph_objects as go

from fin_pocket.cli import main, parse_args, _cli_entry
from fin_pocket.chart import Chart


def _sample_df(n=100):
    np.random.seed(42)
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


# ---------- __init__.py ----------

class TestInit:
    def test_version_is_string(self):
        import fin_pocket
        assert isinstance(fin_pocket.__version__, str)

    def test_version_fallback(self):
        from importlib.metadata import PackageNotFoundError
        with patch("importlib.metadata.version", side_effect=PackageNotFoundError("x")):
            import fin_pocket
            importlib.reload(fin_pocket)
            assert fin_pocket.__version__ == "0.0.0.dev0"
        importlib.reload(fin_pocket)


# ---------- __main__.py ----------

class TestMainModule:
    @patch("fin_pocket.cli._cli_entry")
    def test_main_module_calls_cli_entry(self, mock_entry):
        import fin_pocket.__main__  # noqa: F401


# ---------- cli.main() ----------

class TestCLIMain:
    @patch("fin_pocket.cli.Chart")
    @patch("fin_pocket.cli.DataProvider")
    def test_main_daily_defaults(self, MockProvider, MockChart, capsys):
        mock_provider = MagicMock()
        mock_provider.fetch.return_value = _sample_df()
        MockProvider.return_value = mock_provider

        mock_chart_instance = MagicMock()
        mock_chart_instance.add_signal.return_value = mock_chart_instance
        MockChart.return_value = mock_chart_instance

        args = parse_args(["AAPL"])
        main(args)

        MockProvider.assert_called_once_with("AAPL")
        mock_chart_instance.show.assert_called_once()
        captured = capsys.readouterr()
        assert "Loaded 100 records" in captured.out

    @patch("fin_pocket.cli.Chart")
    @patch("fin_pocket.cli.DataProvider")
    def test_main_hourly(self, MockProvider, MockChart):
        mock_provider = MagicMock()
        mock_provider.fetch.return_value = _sample_df()
        MockProvider.return_value = mock_provider

        mock_chart_instance = MagicMock()
        mock_chart_instance.add_signal.return_value = mock_chart_instance
        MockChart.return_value = mock_chart_instance

        args = parse_args(["TSLA", "--timeframe", "hourly"])
        main(args)

        mock_provider.fetch.assert_called_once_with(period="60d", interval="1h")

    @patch("fin_pocket.cli.Chart")
    @patch("fin_pocket.cli.DataProvider")
    def test_main_output_file(self, MockProvider, MockChart, capsys):
        mock_provider = MagicMock()
        mock_provider.fetch.return_value = _sample_df()
        MockProvider.return_value = mock_provider

        mock_chart_instance = MagicMock()
        mock_chart_instance.add_signal.return_value = mock_chart_instance
        MockChart.return_value = mock_chart_instance

        args = parse_args(["MSFT", "--output", "test.html"])
        main(args)

        mock_chart_instance.save.assert_called_once_with("test.html")
        captured = capsys.readouterr()
        assert "Chart saved to test.html" in captured.out

    @patch("fin_pocket.cli.DataProvider")
    def test_main_connection_error(self, MockProvider, capsys):
        mock_provider = MagicMock()
        mock_provider.fetch.side_effect = ConnectionError("Network failed")
        MockProvider.return_value = mock_provider

        args = parse_args(["FAIL"])
        main(args)

        captured = capsys.readouterr()
        assert "Error:" in captured.out

    @patch("fin_pocket.cli.DataProvider")
    def test_main_value_error(self, MockProvider, capsys):
        mock_provider = MagicMock()
        mock_provider.fetch.side_effect = ValueError("No data")
        MockProvider.return_value = mock_provider

        args = parse_args(["EMPTY"])
        main(args)

        captured = capsys.readouterr()
        assert "Error:" in captured.out

    @patch("fin_pocket.cli.Chart")
    @patch("fin_pocket.cli.DataProvider")
    def test_main_all_signals_disabled(self, MockProvider, MockChart):
        mock_provider = MagicMock()
        mock_provider.fetch.return_value = _sample_df()
        MockProvider.return_value = mock_provider

        mock_chart_instance = MagicMock()
        mock_chart_instance.add_signal.return_value = mock_chart_instance
        MockChart.return_value = mock_chart_instance

        args = parse_args([
            "AAPL",
            "--no-ma", "--no-ma-cross", "--no-rsi", "--no-rsi-divergence",
            "--no-sr", "--no-volume-breakout", "--no-wedge",
            "--no-flag", "--no-fibonacci", "--no-double",
            "--no-macd", "--no-atr", "--no-obv",
        ])
        main(args)

        mock_chart_instance.add_signal.assert_not_called()
        mock_chart_instance.show.assert_called_once()

    @patch("fin_pocket.cli.Chart")
    @patch("fin_pocket.cli.DataProvider")
    def test_main_hourly_all_signals(self, MockProvider, MockChart):
        mock_provider = MagicMock()
        mock_provider.fetch.return_value = _sample_df()
        MockProvider.return_value = mock_provider

        mock_chart_instance = MagicMock()
        mock_chart_instance.add_signal.return_value = mock_chart_instance
        MockChart.return_value = mock_chart_instance

        args = parse_args(["AAPL", "--timeframe", "hourly"])
        main(args)

        assert mock_chart_instance.add_signal.call_count >= 8

    @patch("fin_pocket.cli.Chart")
    @patch("fin_pocket.cli.DataProvider")
    def test_main_with_bb_enabled(self, MockProvider, MockChart):
        mock_provider = MagicMock()
        mock_provider.fetch.return_value = _sample_df()
        MockProvider.return_value = mock_provider

        mock_chart_instance = MagicMock()
        mock_chart_instance.add_signal.return_value = mock_chart_instance
        MockChart.return_value = mock_chart_instance

        args = parse_args(["AAPL", "--bb"])
        main(args)

        signal_types = [
            type(c.args[0]).__name__
            for c in mock_chart_instance.add_signal.call_args_list
        ]
        assert "BollingerBands" in signal_types

    @patch("fin_pocket.cli.main")
    def test_cli_entry(self, mock_main):
        with patch("fin_pocket.cli.parse_args") as mock_parse:
            mock_parse.return_value = MagicMock()
            _cli_entry()
            mock_main.assert_called_once()


# ---------- Chart show / save ----------

class TestChartShowSave:
    def test_show_calls_fig_show(self):
        df = _sample_df()
        chart = Chart(df, ticker="TEST")
        with patch.object(go.Figure, "show") as mock_show:
            chart.show()
            mock_show.assert_called_once()

    def test_save_writes_html(self, tmp_path):
        df = _sample_df()
        chart = Chart(df, ticker="TEST")
        path = str(tmp_path / "chart.html")
        chart.save(path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "<html>" in content.lower() or "plotly" in content.lower()

    def test_build_no_display_days(self):
        df = _sample_df(50)
        chart = Chart(df, ticker="TEST", display_days=None)
        fig = chart.build()
        assert isinstance(fig, go.Figure)

    def test_build_price_range_zero(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {
                "Open": [100.0] * n,
                "High": [100.0] * n,
                "Low": [100.0] * n,
                "Close": [100.0] * n,
                "Volume": [1_000_000] * n,
            },
            index=dates,
        )
        chart = Chart(df, ticker="FLAT")
        fig = chart.build()
        assert isinstance(fig, go.Figure)

    def test_build_price_zero_everywhere(self):
        n = 50
        dates = pd.bdate_range("2024-01-02", periods=n)
        df = pd.DataFrame(
            {
                "Open": [0.0] * n,
                "High": [0.0] * n,
                "Low": [0.0] * n,
                "Close": [0.0] * n,
                "Volume": [0] * n,
            },
            index=dates,
        )
        chart = Chart(df, ticker="ZERO")
        fig = chart.build()
        assert isinstance(fig, go.Figure)
