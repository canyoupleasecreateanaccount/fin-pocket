"""
fin-pocket: Technical analysis signal visualization tool.

Usage:
    fin-pocket AAPL
    fin-pocket GOOG --timeframe hourly
    fin-pocket MSFT --no-wedge --no-rsi
    fin-pocket TSLA --output chart.html
"""

import argparse

from fin_pocket.data import DataProvider
from fin_pocket.signals import (
    MovingAverages,
    MACrossover,
    RSI,
    RSIDivergence,
    SupportResistance,
    Wedge,
    VolumeBreakout,
    Pennant,
    Fibonacci,
)
from fin_pocket.chart import Chart


TIMEFRAME_CONFIG = {
    "daily": {
        "interval": "1d",
        "period": "3y",
        "display_bars": 378,
    },
    "hourly": {
        "interval": "1h",
        "period": "60d",
        "display_bars": 500,
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fin-pocket",
        description="Technical analysis signal visualization for stocks.",
        epilog="Example: fin-pocket AAPL --timeframe daily --no-wedge",
    )

    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol (e.g. AAPL, GOOG, MSFT)",
    )
    parser.add_argument(
        "-t", "--timeframe",
        choices=["daily", "hourly"],
        default="daily",
        help="Chart timeframe (default: daily)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Save chart to HTML file instead of opening in browser",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1000,
        help="Chart height in pixels (default: 1000)",
    )

    signals_group = parser.add_argument_group("signals", "Enable or disable individual signals")
    signals_group.add_argument("--no-ma", action="store_true", help="Disable Moving Averages")
    signals_group.add_argument("--no-ma-cross", action="store_true", help="Disable MA Crossover (Golden/Death Cross)")
    signals_group.add_argument("--no-rsi", action="store_true", help="Disable RSI")
    signals_group.add_argument("--rsi-divergence", action="store_true", help="Enable RSI Divergence (off by default)")
    signals_group.add_argument("--no-sr", action="store_true", help="Disable Support/Resistance levels")
    signals_group.add_argument("--no-volume-breakout", action="store_true", help="Disable Volume Breakout")
    signals_group.add_argument("--no-wedge", action="store_true", help="Disable Wedge patterns")
    signals_group.add_argument("--no-flag", action="store_true", help="Disable Flag & Pennant patterns")
    signals_group.add_argument("--no-fibonacci", action="store_true", help="Disable Fibonacci Retracement")

    return parser.parse_args(argv)


def main(args: argparse.Namespace) -> None:
    config = TIMEFRAME_CONFIG.get(args.timeframe, TIMEFRAME_CONFIG["daily"])
    is_hourly = args.timeframe == "hourly"

    provider = DataProvider(args.ticker)
    data = provider.fetch(period=config["period"], interval=config["interval"])

    print(f"Loaded {len(data)} records for {args.ticker} ({args.timeframe})")
    print(f"Period: {data.index[0]} — {data.index[-1]}")

    chart = Chart(
        data,
        ticker=f"{args.ticker} ({args.timeframe})",
        display_days=config["display_bars"],
        height=args.height,
    )

    if not args.no_ma:
        if is_hourly:
            chart.add_signal(MovingAverages(periods=[20, 50, 100]))
        else:
            chart.add_signal(MovingAverages())

    if not args.no_ma_cross:
        chart.add_signal(MACrossover())

    if not args.no_rsi:
        chart.add_signal(RSI())

    if args.rsi_divergence:
        chart.add_signal(RSIDivergence())

    if not args.no_sr:
        if is_hourly:
            chart.add_signal(SupportResistance(lookback=5, tolerance_pct=0.8, max_levels=3))
        else:
            chart.add_signal(SupportResistance())

    if not args.no_volume_breakout:
        if is_hourly:
            chart.add_signal(VolumeBreakout(vol_period=20, vol_threshold=2.0))
        else:
            chart.add_signal(VolumeBreakout())

    if not args.no_wedge:
        if is_hourly:
            chart.add_signal(Wedge(lookback=4, min_span=15, max_span=60))
        else:
            chart.add_signal(Wedge())

    if not args.no_flag:
        if is_hourly:
            chart.add_signal(
                Pennant(
                    lookback=3,
                    min_pole_bars=3,
                    max_pole_bars=15,
                    min_pole_move_pct=3.0,
                    min_body_bars=5,
                    max_body_bars=20,
                )
            )
        else:
            chart.add_signal(Pennant())

    if not args.no_fibonacci:
        if is_hourly:
            chart.add_signal(Fibonacci(lookback=5, min_move_pct=3.0, recent_bars=150))
        else:
            chart.add_signal(Fibonacci())

    if args.output:
        chart.save(args.output)
        print(f"Chart saved to {args.output}")
    else:
        chart.show()


def _cli_entry():
    """Entry point for the installed package script."""
    main(parse_args())
