import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


class RSIDivergence(BaseSignal):
    """
    Detects divergences between RSI and price.
    
    Bullish divergence: price makes lower low, RSI makes higher low
    Bearish divergence: price makes higher high, RSI makes lower high
    """
    
    def __init__(self, rsi_period: int = 14, lookback: int = 5, min_swing_pct: float = 1.0):
        """
        Args:
            rsi_period: Period for RSI
            lookback: Number of candles to search for local extrema
            min_swing_pct: Minimum difference between extrema in percentage
        """
        self.rsi_period = rsi_period
        self.lookback = lookback
        self.min_swing_pct = min_swing_pct
    
    @property
    def name(self) -> str:
        return "RSI Divergence"
    
    def _calculate_rsi(self, close: pd.Series) -> pd.Series:
        """Calculates RSI if it doesn't exist yet."""
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.rsi_period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.rsi_period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))
    
    def _find_swing_lows(self, series: pd.Series) -> pd.Series:
        """Finds local minima."""
        swing_lows = pd.Series(False, index=series.index)
        
        for i in range(self.lookback, len(series) - self.lookback):
            window = series.iloc[i - self.lookback:i + self.lookback + 1]
            if series.iloc[i] == window.min():
                swing_lows.iloc[i] = True
        
        return swing_lows
    
    def _find_swing_highs(self, series: pd.Series) -> pd.Series:
        """Finds local maxima."""
        swing_highs = pd.Series(False, index=series.index)
        
        for i in range(self.lookback, len(series) - self.lookback):
            window = series.iloc[i - self.lookback:i + self.lookback + 1]
            if series.iloc[i] == window.max():
                swing_highs.iloc[i] = True
        
        return swing_highs
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Finds divergences."""
        df = data.copy()
        
        if "RSI" not in df.columns:
            df["RSI"] = self._calculate_rsi(df["Close"])
        
        df["bullish_divergence"] = False
        df["bearish_divergence"] = False
        df["div_price_start"] = np.nan
        df["div_price_end"] = np.nan
        df["div_rsi_start"] = np.nan
        df["div_rsi_end"] = np.nan
        df["div_start_idx"] = pd.NaT
        
        price_lows = self._find_swing_lows(df["Low"])
        price_highs = self._find_swing_highs(df["High"])
        rsi_lows = self._find_swing_lows(df["RSI"])
        rsi_highs = self._find_swing_highs(df["RSI"])
        
        low_indices = df.index[price_lows].tolist()
        for i, current_idx in enumerate(low_indices[1:], 1):
            prev_idx = low_indices[i - 1]
            
            current_price = df.loc[current_idx, "Low"]
            prev_price = df.loc[prev_idx, "Low"]
            current_rsi = df.loc[current_idx, "RSI"]
            prev_rsi = df.loc[prev_idx, "RSI"]
            
            price_diff_pct = ((prev_price - current_price) / prev_price) * 100
            
            if (current_price < prev_price and 
                current_rsi > prev_rsi and 
                price_diff_pct >= self.min_swing_pct):
                df.loc[current_idx, "bullish_divergence"] = True
                df.loc[current_idx, "div_price_start"] = prev_price
                df.loc[current_idx, "div_price_end"] = current_price
                df.loc[current_idx, "div_rsi_start"] = prev_rsi
                df.loc[current_idx, "div_rsi_end"] = current_rsi
                df.loc[current_idx, "div_start_idx"] = prev_idx
        
        high_indices = df.index[price_highs].tolist()
        for i, current_idx in enumerate(high_indices[1:], 1):
            prev_idx = high_indices[i - 1]
            
            current_price = df.loc[current_idx, "High"]
            prev_price = df.loc[prev_idx, "High"]
            current_rsi = df.loc[current_idx, "RSI"]
            prev_rsi = df.loc[prev_idx, "RSI"]
            
            price_diff_pct = ((current_price - prev_price) / prev_price) * 100
            
            if (current_price > prev_price and 
                current_rsi < prev_rsi and 
                price_diff_pct >= self.min_swing_pct):
                df.loc[current_idx, "bearish_divergence"] = True
                df.loc[current_idx, "div_price_start"] = prev_price
                df.loc[current_idx, "div_price_end"] = current_price
                df.loc[current_idx, "div_rsi_start"] = prev_rsi
                df.loc[current_idx, "div_rsi_end"] = current_rsi
                df.loc[current_idx, "div_start_idx"] = prev_idx
        
        return df
    
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        """Adds divergence markers to the chart."""
        bullish = data[data["bullish_divergence"]]
        bearish = data[data["bearish_divergence"]]
        
        if not bullish.empty:
            fig.add_trace(
                go.Scatter(
                    x=bullish.index,
                    y=bullish["Low"] * 0.97,
                    mode="markers",
                    name="Bullish Divergence",
                    marker=dict(
                        symbol="triangle-up",
                        size=12,
                        color="#00E676",
                        line=dict(color="#000", width=1),
                    ),
                    hovertemplate=(
                        "Bullish Divergence<br>"
                        "Price: Lower Low<br>"
                        "RSI: Higher Low<br>"
                        "Date: %{x}<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )
            
            for idx, row_data in bullish.iterrows():
                if pd.notna(row_data["div_start_idx"]):
                    start_idx = row_data["div_start_idx"]
                    fig.add_trace(
                        go.Scatter(
                            x=[start_idx, idx],
                            y=[row_data["div_price_start"], row_data["div_price_end"]],
                            mode="lines",
                            line=dict(color="#00E676", width=1, dash="dot"),
                            showlegend=False,
                            hoverinfo="skip",
                        ),
                        row=row,
                        col=1,
                    )
        
        if not bearish.empty:
            fig.add_trace(
                go.Scatter(
                    x=bearish.index,
                    y=bearish["High"] * 1.03,
                    mode="markers",
                    name="Bearish Divergence",
                    marker=dict(
                        symbol="triangle-down",
                        size=12,
                        color="#FF5252",
                        line=dict(color="#000", width=1),
                    ),
                    hovertemplate=(
                        "Bearish Divergence<br>"
                        "Price: Higher High<br>"
                        "RSI: Lower High<br>"
                        "Date: %{x}<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )
            
            for idx, row_data in bearish.iterrows():
                if pd.notna(row_data["div_start_idx"]):
                    start_idx = row_data["div_start_idx"]
                    fig.add_trace(
                        go.Scatter(
                            x=[start_idx, idx],
                            y=[row_data["div_price_start"], row_data["div_price_end"]],
                            mode="lines",
                            line=dict(color="#FF5252", width=1, dash="dot"),
                            showlegend=False,
                            hoverinfo="skip",
                        ),
                        row=row,
                        col=1,
                    )
        
        return fig
