import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


class VolumeBreakout(BaseSignal):
    """
    Detects support/resistance level breakouts with volume confirmation.
    
    Bullish signal: price closes above resistance + volume > 1.5x average
    Bearish signal: price closes below support + volume > 1.5x average
    """
    
    def __init__(
        self,
        sr_lookback: int = 10,
        sr_tolerance_pct: float = 1.5,
        sr_min_touches: int = 2,
        vol_period: int = 50,
        vol_threshold: float = 1.5,
        recent_bars: int | None = 400,
    ):
        self.sr_lookback = sr_lookback
        self.sr_tolerance_pct = sr_tolerance_pct
        self.sr_min_touches = sr_min_touches
        self.vol_period = vol_period
        self.vol_threshold = vol_threshold
        self.recent_bars = recent_bars
    
    @property
    def name(self) -> str:
        return "Volume Breakout"
    
    def _find_sr_levels(self, data: pd.DataFrame) -> list[dict]:
        """Finds S/R levels via pivot points and clustering."""
        recent = data.tail(self.recent_bars) if self.recent_bars and len(data) > self.recent_bars else data
        highs = recent["High"].values
        lows = recent["Low"].values
        n = len(recent)
        lb = self.sr_lookback
        current_price = data["Close"].iloc[-1]
        
        pivots = []
        for i in range(lb, n - lb):
            h_win = highs[i - lb:i + lb + 1]
            if highs[i] == h_win.max():
                pivots.append(highs[i])
            l_win = lows[i - lb:i + lb + 1]
            if lows[i] == l_win.min():
                pivots.append(lows[i])
        
        if not pivots:
            return []
        
        pivots.sort()
        clusters = []
        i = 0
        while i < len(pivots):
            group = [pivots[i]]
            j = i + 1
            while j < len(pivots):
                if abs(pivots[j] - group[0]) / group[0] * 100 <= self.sr_tolerance_pct:
                    group.append(pivots[j])
                    j += 1
                else:
                    break
            
            if len(group) >= self.sr_min_touches:
                level = float(np.mean(group))
                dist_pct = abs(level - current_price) / current_price
                clusters.append({
                    "level": level,
                    "touches": len(group),
                    "score": len(group) / (1 + dist_pct * 10),
                })
            i = j
        
        clusters.sort(key=lambda x: -x["score"])
        return clusters[:10]
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        levels = self._find_sr_levels(df)
        
        avg_vol = df["Volume"].rolling(window=self.vol_period, min_periods=20).mean()
        high_vol = df["Volume"] > avg_vol * self.vol_threshold
        
        df["vol_breakout_buy"] = False
        df["vol_breakout_sell"] = False
        df["vol_ratio"] = df["Volume"] / avg_vol.replace(0, 1)
        
        closes = df["Close"].values
        prev_closes = np.roll(closes, 1)
        prev_closes[0] = closes[0]
        
        for level_info in levels:
            level = level_info["level"]
            
            breakout_up = (prev_closes < level * 1.005) & (closes > level * 1.005)
            breakout_down = (prev_closes > level * 0.995) & (closes < level * 0.995)
            
            df.loc[breakout_up & high_vol, "vol_breakout_buy"] = True
            df.loc[breakout_down & high_vol, "vol_breakout_sell"] = True
        
        buy_count = df["vol_breakout_buy"].sum()
        sell_count = df["vol_breakout_sell"].sum()
        print(f"[VolumeBreakout] {buy_count} buy, {sell_count} sell signals")
        
        return df
    
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        buys = data[data["vol_breakout_buy"]]
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys.index, y=buys["Low"] * 0.98,
                mode="markers",
                marker=dict(size=12, color="#00E676", symbol="triangle-up", 
                           line=dict(width=1, color="white")),
                name="Vol Breakout ↑",
                hovertemplate="Vol Breakout UP<br>Vol: %{customdata:.1f}x avg<extra></extra>",
                customdata=buys["vol_ratio"],
            ), row=row, col=1)
        
        sells = data[data["vol_breakout_sell"]]
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells.index, y=sells["High"] * 1.02,
                mode="markers",
                marker=dict(size=12, color="#FF5252", symbol="triangle-down",
                           line=dict(width=1, color="white")),
                name="Vol Breakout ↓",
                hovertemplate="Vol Breakout DOWN<br>Vol: %{customdata:.1f}x avg<extra></extra>",
                customdata=sells["vol_ratio"],
            ), row=row, col=1)
        
        return fig
