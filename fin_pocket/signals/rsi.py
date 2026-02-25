import pandas as pd
import plotly.graph_objects as go
from .base import BaseSignal


class RSI(BaseSignal):
    """
    Relative Strength Index (RSI).
    
    Oscillator that shows trend strength from 0 to 100.
    - RSI > 70: overbought (possible reversal down)
    - RSI < 30: oversold (possible reversal up)
    """
    
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    @property
    def name(self) -> str:
        return f"RSI ({self.period})"
    
    @property
    def panel(self) -> str:
        return "separate"
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates RSI and signals."""
        df = data.copy()
        
        delta = df["Close"].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        df["RSI"] = 100 - (100 / (1 + rs))
        
        df["RSI_prev"] = df["RSI"].shift(1)
        df["rsi_buy_signal"] = (df["RSI"] < self.oversold) & (df["RSI_prev"] >= self.oversold)
        df["rsi_sell_signal"] = (df["RSI"] > self.overbought) & (df["RSI_prev"] <= self.overbought)
        
        return df
    
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        """Adds RSI to a separate subplot."""
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["RSI"],
                mode="lines",
                name="RSI",
                line=dict(color="#AB47BC", width=1.5),
                hovertemplate="RSI: %{y:.1f}<extra></extra>",
            ),
            row=row,
            col=1,
        )
        
        fig.add_hline(
            y=self.overbought,
            line_dash="dash",
            line_color="#EF5350",
            opacity=0.5,
            row=row,
            col=1,
        )
        fig.add_hline(
            y=self.oversold,
            line_dash="dash",
            line_color="#26A69A",
            opacity=0.5,
            row=row,
            col=1,
        )
        
        fig.add_hrect(
            y0=self.overbought,
            y1=100,
            fillcolor="#EF5350",
            opacity=0.1,
            line_width=0,
            row=row,
            col=1,
        )
        fig.add_hrect(
            y0=0,
            y1=self.oversold,
            fillcolor="#26A69A",
            opacity=0.1,
            line_width=0,
            row=row,
            col=1,
        )
        
        fig.update_yaxes(
            title_text="RSI",
            range=[0, 100],
            row=row,
            col=1,
        )
        
        buy_signals = data[data["rsi_buy_signal"]]
        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals["RSI"],
                    mode="markers",
                    name="RSI Buy",
                    marker=dict(
                        symbol="triangle-up",
                        size=10,
                        color="#26A69A",
                        line=dict(color="#fff", width=1),
                    ),
                    hovertemplate="BUY Signal<br>RSI: %{y:.1f}<extra></extra>",
                ),
                row=row,
                col=1,
            )
        
        sell_signals = data[data["rsi_sell_signal"]]
        if not sell_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=sell_signals.index,
                    y=sell_signals["RSI"],
                    mode="markers",
                    name="RSI Sell",
                    marker=dict(
                        symbol="triangle-down",
                        size=10,
                        color="#EF5350",
                        line=dict(color="#fff", width=1),
                    ),
                    hovertemplate="SELL Signal<br>RSI: %{y:.1f}<extra></extra>",
                ),
                row=row,
                col=1,
            )
        
        return fig
