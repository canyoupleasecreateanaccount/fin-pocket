# fin-pocket

[![PyPI version](https://img.shields.io/pypi/v/fin-pocket)](https://pypi.org/project/fin-pocket/)
[![Python](https://img.shields.io/pypi/pyversions/fin-pocket)](https://pypi.org/project/fin-pocket/)
[![CI](https://github.com/canyoupleasecreateanaccount/fin-pocket/actions/workflows/ci.yml/badge.svg)](https://github.com/canyoupleasecreateanaccount/fin-pocket/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/canyoupleasecreateanaccount/fin-pocket/branch/main/graph/badge.svg)](https://codecov.io/gh/canyoupleasecreateanaccount/fin-pocket)
[![Downloads](https://img.shields.io/pypi/dm/fin-pocket)](https://pypi.org/project/fin-pocket/)
[![License](https://img.shields.io/badge/license-proprietary-red)](LICENSE)

Technical analysis signal visualization tool for stocks. Fetches historical data from Yahoo Finance and renders interactive charts with configurable technical signals.

> **Quick tip:** Not sure whether to buy a stock? Generate a chart, take a screenshot, and send it to any LLM (ChatGPT, Claude, Gemini, etc.) with a question like *"Based on these technical signals, is it a good time to buy? What are the key levels to watch?"* — you'll get an instant analysis without needing to read the chart yourself.

![Chart Preview](https://raw.githubusercontent.com/canyoupleasecreateanaccount/fin-pocket/main/assets/chart_preview.png)

## Features

| Signal | Description | Default |
|--------|-------------|---------|
| **Moving Averages** | MA 50 / 100 / 200 (configurable periods) | On |
| **MA Crossover** | Golden Cross & Death Cross detection | On |
| **RSI** | Relative Strength Index with overbought/oversold zones | On |
| **RSI Divergence** | Bullish/bearish divergence between price and RSI | On |
| **Support / Resistance** | Pivot-based S/R level detection with clustering | On |
| **Volume Breakout** | S/R breakout confirmed by above-average volume | On |
| **Wedge** | Rising and falling wedge pattern detection | On |
| **Flag & Pennant** | Flagpole + parallel channel or converging triangle | On |
| **Double Top/Bottom** | Double top (bearish) and double bottom (bullish) reversal patterns | On |
| **Bollinger Bands** | Volatility envelope around a 20-period SMA (±2 std dev) | Off |
| **MACD** | Moving Average Convergence Divergence (12, 26, 9) with crossover signals | On |
| **ATR** | Average True Range — 14-period volatility measure | On |
| **OBV** | On-Balance Volume with 20-period MA overlay | On |
| **Fibonacci Retracement** | Key retracement levels from the last major swing | On |

## Signal Descriptions

### Moving Averages (MA)
Simple Moving Averages plotted for 50, 100, and 200 periods (configurable). They smooth out price action and help identify the overall trend direction. When the price is above MAs — the trend is bullish; below — bearish.

### MA Crossover (Golden / Death Cross)
Detects when the short-term MA (50) crosses the long-term MA (200). A **Golden Cross** (50 crosses above 200) is a bullish signal, while a **Death Cross** (50 crosses below 200) is a bearish signal. Markers are plotted at the crossover points.

### RSI (Relative Strength Index)
A momentum oscillator (0–100) that measures the speed and magnitude of price changes over 14 periods. Values above 70 indicate overbought conditions; below 30 — oversold. Displayed on a separate panel with shaded zones.

### RSI Divergence
Detects divergences between price and RSI — when price makes a new high/low but RSI does not confirm. **Bullish divergence** (price makes lower low, RSI makes higher low) suggests potential reversal up. **Bearish divergence** is the opposite.

### Support / Resistance
Identifies key horizontal price levels where buying (support) or selling (resistance) pressure has historically clustered. Uses pivot-based detection with configurable tolerance and clustering to avoid duplicate levels.

### Volume Breakout
Flags breakouts through Support/Resistance levels that are confirmed by above-average volume. Higher volume on a breakout increases the probability that the move is genuine rather than a false break.

### Wedge
Detects **rising wedges** (bearish) and **falling wedges** (bullish) — converging trendlines where both highs and lows move in the same direction. A breakout from the wedge in the opposite direction is plotted.

### Flag & Pennant
Identifies continuation patterns: a sharp move (flagpole) followed by a consolidation (flag = parallel channel, pennant = converging triangle). Patterns are highlighted with trendlines on the chart.

### Double Top / Bottom
Recognizes classic reversal patterns. A **double top** occurs when price reaches the same high twice and fails to break through — bearish. A **double bottom** is the inverse — bullish. Neckline and confirmation levels are plotted.

### Bollinger Bands
Three lines plotted around a 20-period SMA: the upper band at +2 standard deviations and the lower band at −2 standard deviations. When the bands contract, volatility is low (squeeze); when they expand, a significant move may follow. Disabled by default.

### MACD (Moving Average Convergence Divergence)
Calculated as the difference between the 12-period and 26-period EMAs. A 9-period EMA of the MACD line (signal line) and a histogram (MACD − signal) are also plotted. **Bullish crossover**: MACD crosses above signal. **Bearish crossover**: MACD crosses below signal. Crossover markers are displayed on the chart.

### ATR (Average True Range)
Measures market volatility as the 14-period rolling average of True Range (the greatest of: High−Low, |High−prevClose|, |Low−prevClose|). Higher ATR = more volatile market. Plotted on a separate panel.

### OBV (On-Balance Volume)
A cumulative volume indicator: volume is added when close > previous close and subtracted when close < previous close. Rising OBV confirms an uptrend; falling OBV confirms a downtrend. A 20-period MA overlay is included for smoothing.

### Fibonacci Retracement
Plots key retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%) based on the last major price swing. Traders watch these levels for potential support/resistance during pullbacks.

## Installation

From PyPI:

```bash
pip install fin-pocket
```

From source:

```bash
git clone git@github.com:canyoupleasecreateanaccount/fin-pocket.git && cd fin-pocket
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
pip install -e ".[dev]"
```

## Usage

### Basic

```bash
fin-pocket AAPL
```

or via module:

```bash
python -m fin_pocket AAPL
```

### Options

```
positional arguments:
  ticker                Stock ticker symbol (e.g. AAPL, GOOG, MSFT)

options:
  -t, --timeframe {daily,hourly}   Chart timeframe (default: daily)
  -o, --output FILE                Save chart to HTML file
  --height PIXELS                  Chart height in pixels (default: 1000)

signals:
  --no-ma               Disable Moving Averages
  --no-ma-cross         Disable MA Crossover
  --no-rsi              Disable RSI
  --no-rsi-divergence   Disable RSI Divergence
  --no-sr               Disable Support/Resistance levels
  --no-volume-breakout  Disable Volume Breakout
  --no-wedge            Disable Wedge patterns
  --no-flag             Disable Flag & Pennant patterns
  --no-fibonacci        Disable Fibonacci Retracement
  --no-double           Disable Double Top/Bottom
  --bb                  Enable Bollinger Bands (off by default)
  --no-macd             Disable MACD
  --no-atr              Disable ATR
  --no-obv              Disable OBV
```

### Examples

```bash
# Daily chart for Google with all defaults
fin-pocket GOOG

# Hourly chart for Tesla, no wedges
fin-pocket TSLA --timeframe hourly --no-wedge

# Save to file instead of opening browser
fin-pocket MSFT --output msft_chart.html

# Minimal chart — only price and moving averages
fin-pocket AAPL --no-rsi --no-rsi-divergence --no-sr --no-volume-breakout --no-wedge --no-flag --no-fibonacci --no-double --no-macd --no-atr --no-obv
```
 
## Project Structure

```
fin-pocket/
├── fin_pocket/
│   ├── __init__.py      # Package version
│   ├── __main__.py      # python -m fin_pocket
│   ├── cli.py           # CLI entry point
│   ├── chart.py         # Plotly chart builder
│   ├── data/
│   │   ├── __init__.py
│   │   └── provider.py  # Yahoo Finance data provider
│   └── signals/
│       ├── __init__.py
│       ├── base.py      # Abstract base signal class
│       ├── moving_averages.py
│       ├── ma_crossover.py
│       ├── rsi.py
│       ├── rsi_divergence.py
│       ├── support_resistance.py
│       ├── volume_breakout.py
│       ├── wedge.py
│       ├── pennant.py   # Flag & Pennant
│       ├── double_top_bottom.py
│       ├── bollinger_bands.py
│       ├── macd.py
│       ├── atr.py
│       ├── obv.py
│       └── fibonacci.py # Fibonacci Retracement
├── tests/
│   └── ...
├── pyproject.toml
├── LICENSE
└── README.md
```

## Running Tests

```bash
pytest
pytest --cov=fin_pocket
```


## Dependencies

- **yfinance** — historical market data from Yahoo Finance
- **pandas** — data manipulation
- **plotly** — interactive charting
- **numpy** — numerical computations

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to submit pull requests.

## Contact

Email: solveme.solutions@gmail.com

## Support

<a href="https://www.buymeacoffee.com/yourCrowley" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="50" ></a>

## License

Proprietary — for personal use only. See [LICENSE](LICENSE).
