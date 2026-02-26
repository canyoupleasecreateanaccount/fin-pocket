import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .base import BaseSignal


class OBV(BaseSignal):
    """
    On-Balance Volume — cumulative volume indicator.

    When close > prev_close: add volume.
    When close < prev_close: subtract volume.
    When close == prev_close: no change.
    """

    def __init__(self, ma_period: int = 20):
        self.ma_period = ma_period

    @property
    def name(self) -> str:
        return "OBV"

    @property
    def panel(self) -> str:
        return "separate"

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        direction = np.sign(df["Close"].diff())
        direction.iloc[0] = 0

        df["OBV"] = (direction * df["Volume"]).cumsum()
        df["OBV_MA"] = df["OBV"].rolling(window=self.ma_period, min_periods=1).mean()

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["OBV"],
                mode="lines",
                name="OBV",
                line=dict(color="#26C6DA", width=1.5),
                hovertemplate="OBV: %{y:,.0f}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["OBV_MA"],
                mode="lines",
                name=f"OBV MA{self.ma_period}",
                line=dict(color="#FFA726", width=1, dash="dash"),
                hovertemplate=f"OBV MA{self.ma_period}: %{{y:,.0f}}<extra></extra>",
            ),
            row=row,
            col=1,
        )

        fig.update_yaxes(title_text="OBV", row=row, col=1)

        last = data.iloc[-1]
        x_last = data.index[-1]
        for val, color, label, yoff in [
            (last["OBV"], "#26C6DA", "OBV", 8),
            (last["OBV_MA"], "#FFA726", f"MA{self.ma_period}", -8),
        ]:
            fig.add_annotation(
                x=x_last, y=val,
                text=f" {label}: {val:,.0f}",
                showarrow=False, xanchor="left", xshift=5, yshift=yoff,
                font=dict(color=color, size=9),
                row=row, col=1,
            )

        return fig
