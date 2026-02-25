import pandas as pd
import plotly.graph_objects as go
from .base import BaseSignal


class MACrossover(BaseSignal):
    """
    Detects Golden Cross and Death Cross.
    
    Golden Cross: short MA crosses long MA from below upward (bullish signal)
    Death Cross: short MA crosses long MA from above downward (bearish signal)
    """
    
    def __init__(self, short_period: int = 50, long_period: int = 200):
        self.short_period = short_period
        self.long_period = long_period
    
    @property
    def name(self) -> str:
        return f"MA Crossover ({self.short_period}/{self.long_period})"
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates MA and finds crossovers."""
        df = data.copy()
        
        short_col = f"MA_{self.short_period}"
        long_col = f"MA_{self.long_period}"
        
        if short_col not in df.columns:
            df[short_col] = df["Close"].rolling(window=self.short_period).mean()
        if long_col not in df.columns:
            df[long_col] = df["Close"].rolling(window=self.long_period).mean()
        
        df["_ma_diff"] = df[short_col] - df[long_col]
        df["_ma_diff_prev"] = df["_ma_diff"].shift(1)
        
        df["golden_cross"] = (df["_ma_diff"] > 0) & (df["_ma_diff_prev"] <= 0)
        df["death_cross"] = (df["_ma_diff"] < 0) & (df["_ma_diff_prev"] >= 0)
        
        df.drop(columns=["_ma_diff", "_ma_diff_prev"], inplace=True)
        
        return df
    
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        """Adds crossover markers to the chart."""
        golden = data[data["golden_cross"]]
        death = data[data["death_cross"]]
        
        if not golden.empty:
            fig.add_trace(
                go.Scatter(
                    x=golden.index,
                    y=golden["Low"] * 0.97,
                    mode="markers+text",
                    name="Golden Cross",
                    marker=dict(
                        symbol="triangle-up",
                        size=15,
                        color="#FFD700",
                        line=dict(color="#000", width=1),
                    ),
                    text=["GC"] * len(golden),
                    textposition="bottom center",
                    textfont=dict(size=10, color="#FFD700"),
                    hovertemplate=(
                        "Golden Cross<br>"
                        "Date: %{x}<br>"
                        "Price: %{customdata:.2f}<extra></extra>"
                    ),
                    customdata=golden["Close"],
                ),
                row=row,
                col=1,
            )
        
        if not death.empty:
            fig.add_trace(
                go.Scatter(
                    x=death.index,
                    y=death["High"] * 1.03,
                    mode="markers+text",
                    name="Death Cross",
                    marker=dict(
                        symbol="triangle-down",
                        size=15,
                        color="#DC143C",
                        line=dict(color="#000", width=1),
                    ),
                    text=["DC"] * len(death),
                    textposition="top center",
                    textfont=dict(size=10, color="#DC143C"),
                    hovertemplate=(
                        "Death Cross<br>"
                        "Date: %{x}<br>"
                        "Price: %{customdata:.2f}<extra></extra>"
                    ),
                    customdata=death["Close"],
                ),
                row=row,
                col=1,
            )
        
        return fig
