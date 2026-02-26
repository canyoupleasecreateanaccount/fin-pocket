import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .base import BaseSignal


class MACD(BaseSignal):
    """
    Moving Average Convergence Divergence.

    MACD Line  = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal)
    Histogram   = MACD Line - Signal Line

    Bullish crossover: MACD crosses above signal line.
    Bearish crossover: MACD crosses below signal line.
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    @property
    def name(self) -> str:
        return f"MACD ({self.fast},{self.slow},{self.signal_period})"

    @property
    def panel(self) -> str:
        return "separate"

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        ema_fast = df["Close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=self.slow, adjust=False).mean()

        df["MACD"] = ema_fast - ema_slow
        df["MACD_signal"] = df["MACD"].ewm(span=self.signal_period, adjust=False).mean()
        df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

        prev_hist = df["MACD_hist"].shift(1)
        df["MACD_bull_cross"] = (prev_hist < 0) & (df["MACD_hist"] >= 0)
        df["MACD_bear_cross"] = (prev_hist > 0) & (df["MACD_hist"] <= 0)

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        colors = ["#26A69A" if v >= 0 else "#EF5350" for v in data["MACD_hist"]]

        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["MACD_hist"],
                name="MACD Hist",
                marker_color=colors,
                opacity=0.6,
                hovertemplate="Hist: %{y:.4f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["MACD"],
                mode="lines",
                name="MACD",
                line=dict(color="#2196F3", width=1.5),
                hovertemplate="MACD: %{y:.4f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["MACD_signal"],
                mode="lines",
                name="Signal",
                line=dict(color="#FF9800", width=1.5),
                hovertemplate="Signal: %{y:.4f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        bulls = data[data["MACD_bull_cross"]]
        if not bulls.empty:
            fig.add_trace(
                go.Scatter(
                    x=bulls.index,
                    y=bulls["MACD"],
                    mode="markers",
                    name="MACD Bull Cross",
                    marker=dict(symbol="triangle-up", size=10, color="#26A69A"),
                    hovertemplate="Bullish crossover<br>MACD: %{y:.4f}<extra></extra>",
                ),
                row=row,
                col=1,
            )

        bears = data[data["MACD_bear_cross"]]
        if not bears.empty:
            fig.add_trace(
                go.Scatter(
                    x=bears.index,
                    y=bears["MACD"],
                    mode="markers",
                    name="MACD Bear Cross",
                    marker=dict(symbol="triangle-down", size=10, color="#EF5350"),
                    hovertemplate="Bearish crossover<br>MACD: %{y:.4f}<extra></extra>",
                ),
                row=row,
                col=1,
            )

        fig.add_hline(
            y=0,
            line_dash="dot",
            line_color="rgba(255,255,255,0.3)",
            line_width=1,
            row=row,
            col=1,
        )

        fig.update_yaxes(title_text="MACD", row=row, col=1)

        last = data.iloc[-1]
        x_last = data.index[-1]
        for val, color, label, yoff in [
            (last["MACD"], "#2196F3", "MACD", 8),
            (last["MACD_signal"], "#FF9800", "S", -8),
        ]:
            fig.add_annotation(
                x=x_last, y=val,
                text=f" {label}: {val:.2f}",
                showarrow=False, xanchor="left", xshift=5, yshift=yoff,
                font=dict(color=color, size=9),
                row=row, col=1,
            )

        return fig
