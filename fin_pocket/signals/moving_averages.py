import pandas as pd
import plotly.graph_objects as go
from .base import BaseSignal


class MovingAverages(BaseSignal):
    """Moving Averages signal - MA 50, 100, 200."""
    
    MA_COLORS = {
        20: "#FF9800",   # orange
        50: "#EF5350",   # red
        100: "#2196F3",  # blue
        200: "#4CAF50",  # green
    }
    
    def __init__(self, periods: list[int] = None):
        self.periods = periods or [50, 100, 200]
    
    @property
    def name(self) -> str:
        return "Moving Averages"
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates moving averages."""
        df = data.copy()
        
        for period in self.periods:
            col_name = f"MA_{period}"
            df[col_name] = df["Close"].rolling(window=period).mean()
        
        return df
    
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        """Adds MA lines to the chart."""
        x_last = data.index[-1]
        ma_values = []

        for period in self.periods:
            col_name = f"MA_{period}"
            if col_name not in data.columns:
                continue
            
            color = self.MA_COLORS.get(period, "#9E9E9E")
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[col_name],
                    mode="lines",
                    name=f"MA {period}",
                    line=dict(color=color, width=1.5),
                    hovertemplate=f"MA {period}: %{{y:.2f}}<extra></extra>",
                ),
                row=row,
                col=1,
            )

            last_val = data[col_name].iloc[-1]
            if pd.notna(last_val):
                ma_values.append((last_val, color, f"MA {period}"))

        ma_values.sort(key=lambda t: t[0], reverse=True)
        for i, (val, color, label) in enumerate(ma_values):
            fig.add_annotation(
                x=x_last, y=val,
                text=f" {label}: {val:.2f}",
                showarrow=False, xanchor="left", xshift=100,
                yshift=10 - i * 12,
                font=dict(color=color, size=9),
                row=row, col=1,
            )

        return fig
