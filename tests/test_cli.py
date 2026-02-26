"""Tests for CLI argument parsing."""

from fin_pocket.cli import parse_args


class TestCLI:
    def test_ticker_required(self):
        args = parse_args(["AAPL"])
        assert args.ticker == "AAPL"

    def test_default_timeframe(self):
        args = parse_args(["GOOG"])
        assert args.timeframe == "daily"

    def test_hourly_timeframe(self):
        args = parse_args(["GOOG", "--timeframe", "hourly"])
        assert args.timeframe == "hourly"

    def test_short_timeframe_flag(self):
        args = parse_args(["GOOG", "-t", "hourly"])
        assert args.timeframe == "hourly"

    def test_output_flag(self):
        args = parse_args(["AAPL", "--output", "chart.html"])
        assert args.output == "chart.html"

    def test_height_flag(self):
        args = parse_args(["AAPL", "--height", "800"])
        assert args.height == 800

    def test_default_height(self):
        args = parse_args(["AAPL"])
        assert args.height == 1000

    def test_no_ma_flag(self):
        args = parse_args(["AAPL", "--no-ma"])
        assert args.no_ma is True

    def test_no_rsi_flag(self):
        args = parse_args(["AAPL", "--no-rsi"])
        assert args.no_rsi is True

    def test_rsi_divergence_on_by_default(self):
        args = parse_args(["AAPL"])
        assert args.no_rsi_divergence is False

    def test_rsi_divergence_disable(self):
        args = parse_args(["AAPL", "--no-rsi-divergence"])
        assert args.no_rsi_divergence is True

    def test_all_disable_flags(self):
        args = parse_args([
            "AAPL",
            "--no-ma", "--no-ma-cross", "--no-rsi",
            "--no-rsi-divergence",
            "--no-sr", "--no-volume-breakout", "--no-wedge",
            "--no-flag", "--no-fibonacci", "--no-double",
            "--no-macd", "--no-atr", "--no-obv",
        ])
        assert args.no_ma is True
        assert args.no_ma_cross is True
        assert args.no_rsi is True
        assert args.no_rsi_divergence is True
        assert args.no_sr is True
        assert args.no_volume_breakout is True
        assert args.no_wedge is True
        assert args.no_flag is True
        assert args.no_fibonacci is True
        assert args.no_double is True
        assert args.no_macd is True
        assert args.no_atr is True
        assert args.no_obv is True

    def test_bb_off_by_default(self):
        args = parse_args(["AAPL"])
        assert args.bb is False

    def test_bb_enable(self):
        args = parse_args(["AAPL", "--bb"])
        assert args.bb is True

    def test_all_defaults(self):
        args = parse_args(["AAPL"])
        assert args.no_rsi_divergence is False
        assert args.no_double is False
        assert args.bb is False
        assert args.no_macd is False
        assert args.no_atr is False
        assert args.no_obv is False
