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

    @staticmethod
    def _fmt(value: float) -> str:
        """Format large numbers with K/M/B suffixes."""
        sign = "-" if value < 0 else ""
        v = abs(value)
        if v >= 1e9:
            return f"{sign}{v / 1e9:.2f}B"
        if v >= 1e6:
            return f"{sign}{v / 1e6:.2f}M"
        if v >= 1e3:
            return f"{sign}{v / 1e3:.1f}K"
        return f"{sign}{v:,.0f}"

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

        obv_val = last["OBV"]
        ma_val = last["OBV_MA"]
        obv_on_top = obv_val >= ma_val

        for val, color, label, on_top in [
            (obv_val, "#26C6DA", "OBV", obv_on_top),
            (ma_val, "#FFA726", f"MA{self.ma_period}", not obv_on_top),
        ]:
            fig.add_annotation(
                x=x_last, y=val,
                text=f" {label}: {self._fmt(val)}",
                showarrow=False, xanchor="left", xshift=5,
                yshift=10 if on_top else -10,
                font=dict(color=color, size=9),
                row=row, col=1,
            )

        return fig
