import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


class ATR(BaseSignal):
    """
    Average True Range — measures market volatility.

    True Range = max(H-L, |H-prevClose|, |L-prevClose|)
    ATR = rolling mean of True Range over `period` bars.
    """

    def __init__(self, period: int = 14):
        self.period = period

    @property
    def name(self) -> str:
        return f"ATR ({self.period})"

    @property
    def panel(self) -> str:
        return "separate"

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        high = df["High"]
        low = df["Low"]
        prev_close = df["Close"].shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        df["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["ATR"] = df["TR"].rolling(window=self.period, min_periods=1).mean()

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["ATR"],
                mode="lines",
                name="ATR",
                line=dict(color="#FF9800", width=1.5),
                hovertemplate="ATR: %{y:.2f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.update_yaxes(title_text="ATR", row=row, col=1)

        last_atr = data["ATR"].iloc[-1]
        fig.add_annotation(
            x=data.index[-1], y=last_atr,
            text=f" ATR: {last_atr:.2f}",
            showarrow=False, xanchor="left", xshift=5,
            font=dict(color="#FF9800", size=9),
            row=row, col=1,
        )

        return fig
