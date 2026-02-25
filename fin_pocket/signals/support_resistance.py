import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


class SupportResistance(BaseSignal):
    """
    Finds support and resistance levels.
    
    Uses local extrema and clusters nearby levels.
    """
    
    def __init__(
        self,
        lookback: int = 10,
        tolerance_pct: float = 1.5,
        min_touches: int = 2,
        max_levels: int = 5,
        recent_bars: int | None = 400,
    ):
        self.lookback = lookback
        self.tolerance_pct = tolerance_pct
        self.min_touches = min_touches
        self.max_levels = max_levels
        self.recent_bars = recent_bars
    
    @property
    def name(self) -> str:
        return "Support/Resistance"
    
    def _find_pivot_lows(self, data: pd.DataFrame) -> list[float]:
        """Finds local minima."""
        pivots = []
        lows = data["Low"].values
        
        for i in range(self.lookback, len(lows) - self.lookback):
            window = lows[i - self.lookback:i + self.lookback + 1]
            if lows[i] == window.min():
                pivots.append(lows[i])
        
        return pivots
    
    def _find_pivot_highs(self, data: pd.DataFrame) -> list[float]:
        """Finds local maxima."""
        pivots = []
        highs = data["High"].values
        
        for i in range(self.lookback, len(highs) - self.lookback):
            window = highs[i - self.lookback:i + self.lookback + 1]
            if highs[i] == window.max():
                pivots.append(highs[i])
        
        return pivots
    
    def _cluster_levels(self, levels: list[float], current_price: float) -> list[dict]:
        """Clusters nearby levels and counts touches."""
        if not levels:
            return []
        
        levels = sorted(levels)
        clusters = []
        
        i = 0
        while i < len(levels):
            cluster_levels = [levels[i]]
            j = i + 1
            
            while j < len(levels):
                if cluster_levels[0] != 0 and abs(levels[j] - cluster_levels[0]) / cluster_levels[0] * 100 <= self.tolerance_pct:
                    cluster_levels.append(levels[j])
                    j += 1
                else:
                    break
            
            avg_level = np.mean(cluster_levels)
            min_level = min(cluster_levels)
            max_level = max(cluster_levels)
            touches = len(cluster_levels)
            
            if touches >= self.min_touches:
                level_type = "support" if avg_level < current_price else "resistance"
                clusters.append({
                    "level": avg_level,
                    "level_min": min_level,
                    "level_max": max_level,
                    "touches": touches,
                    "type": level_type,
                    "strength": touches,
                })
            
            i = j
        
        for c in clusters:
            dist_pct = abs(c["level"] - current_price) / current_price
            c["score"] = c["touches"] / (1 + dist_pct * 10)
        
        clusters.sort(key=lambda x: x["score"], reverse=True)
        return clusters[:self.max_levels * 2]
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Finds support and resistance levels."""
        df = data.copy()
        
        recent = df.tail(self.recent_bars) if self.recent_bars and len(df) > self.recent_bars else df
        
        pivot_lows = self._find_pivot_lows(recent)
        pivot_highs = self._find_pivot_highs(recent)
        
        all_pivots = pivot_lows + pivot_highs
        current_price = df["Close"].iloc[-1]
        
        levels = self._cluster_levels(all_pivots, current_price)
        
        df.attrs["support_resistance_levels"] = levels
        
        return df
    
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        """Draws support and resistance levels."""
        levels = data.attrs.get("support_resistance_levels", [])
        
        if not levels:
            return fig
        
        price_min = data["Low"].min()
        price_max = data["High"].max()
        price_range = price_max - price_min
        
        relevant_levels = [l for l in levels 
                          if price_min - price_range * 0.1 <= l["level"] <= price_max + price_range * 0.1]
        
        supports = [l for l in relevant_levels if l["type"] == "support"][:self.max_levels]
        resistances = [l for l in relevant_levels if l["type"] == "resistance"][:self.max_levels]
        
        for i, level in enumerate(supports):
            fig.add_hrect(
                y0=level["level_min"],
                y1=level["level_max"],
                fillcolor="rgba(255, 255, 255, 0.1)",
                line_width=0,
                row=row,
                col=1,
            )
            fig.add_hline(
                y=level["level"],
                line_dash="solid",
                line_color="rgba(255, 255, 255, 0.4)",
                line_width=1,
                annotation_text=f"S{i+1}: {level['level']:.2f}",
                annotation_position="left",
                annotation_font_color="rgba(255, 255, 255, 0.6)",
                annotation_font_size=10,
                row=row,
                col=1,
            )
        
        for i, level in enumerate(resistances):
            fig.add_hrect(
                y0=level["level_min"],
                y1=level["level_max"],
                fillcolor="rgba(255, 255, 255, 0.1)",
                line_width=0,
                row=row,
                col=1,
            )
            fig.add_hline(
                y=level["level"],
                line_dash="solid",
                line_color="rgba(255, 255, 255, 0.4)",
                line_width=1,
                annotation_text=f"R{i+1}: {level['level']:.2f}",
                annotation_position="right",
                annotation_font_color="rgba(255, 255, 255, 0.6)",
                annotation_font_size=10,
                row=row,
                col=1,
            )
        
        return fig
