import pandas as pd
import plotly.graph_objects as go
from .base import BaseSignal


class BollingerBands(BaseSignal):
    """
    Bollinger Bands — volatility envelope around a moving average.

    Middle Band = SMA(period)
    Upper Band  = Middle + std_dev * rolling std
    Lower Band  = Middle - std_dev * rolling std
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev

    @property
    def name(self) -> str:
        return f"BB ({self.period},{self.std_dev})"

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        df["BB_middle"] = df["Close"].rolling(window=self.period, min_periods=1).mean()
        rolling_std = df["Close"].rolling(window=self.period, min_periods=1).std().fillna(0)
        df["BB_upper"] = df["BB_middle"] + self.std_dev * rolling_std
        df["BB_lower"] = df["BB_middle"] - self.std_dev * rolling_std

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["BB_upper"],
                mode="lines",
                name="BB Upper",
                line=dict(color="#7E57C2", width=1, dash="dash"),
                hovertemplate="BB Upper: %{y:.2f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["BB_lower"],
                mode="lines",
                name="BB Lower",
                line=dict(color="#7E57C2", width=1, dash="dash"),
                fill="tonexty",
                fillcolor="rgba(126,87,194,0.08)",
                hovertemplate="BB Lower: %{y:.2f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["BB_middle"],
                mode="lines",
                name="BB Middle",
                line=dict(color="#7E57C2", width=1.5),
                hovertemplate="BB Middle: %{y:.2f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        return fig
