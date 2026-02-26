import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


class Wedge(BaseSignal):
    """
    Detects Wedges.
    
    Each trendline is confirmed by at least 3 touch points (swing pivots).
    Upper line — ceiling (price doesn't break upward).
    Lower line — floor (price doesn't break downward).
    Both lines slope in the same direction and converge.
    """
    
    def __init__(self, lookback: int = 8, min_span: int = 30, max_span: int = 120):
        self.lookback = lookback
        self.min_span = min_span
        self.max_span = max_span
        self._wedges = []
    
    @property
    def name(self) -> str:
        return "Wedge"
    
    def _find_pivots(self, data: pd.DataFrame, pivot_type: str) -> list[dict]:
        pivots = []
        col = "High" if pivot_type == "high" else "Low"
        values = data[col].values
        dates = data.index
        for i in range(self.lookback, len(values) - self.lookback):
            window = values[i - self.lookback:i + self.lookback + 1]
            if pivot_type == "high" and values[i] == window.max():
                pivots.append({"idx": i, "val": values[i], "date": dates[i]})
            elif pivot_type == "low" and values[i] == window.min():
                pivots.append({"idx": i, "val": values[i], "date": dates[i]})
        return pivots
    
    def _validate_trendline(self, raw_values: np.ndarray, pivots: list[dict],
                            i: int, j: int, is_ceiling: bool) -> tuple:
        """
        Validates trendline through pivots[i] and pivots[j].
        
        Checks:
        1. All raw values within 1.5% of the line (boundary)
        2. At least 1 intermediate pivot within 2% of the line (3+ touch points)
        
        Returns (valid, touch_points, slope, intercept).
        """
        p1, p2 = pivots[i], pivots[j]
        span = p2["idx"] - p1["idx"]
        if span <= 0:
            return False, [], 0, 0
        
        slope = (p2["val"] - p1["val"]) / span
        intercept = p1["val"] - slope * p1["idx"]
        
        for k in range(p1["idx"], p2["idx"] + 1):
            line_v = slope * k + intercept
            tol = abs(line_v) * 0.015
            if is_ceiling and raw_values[k] > line_v + tol:
                return False, [], 0, 0
            if not is_ceiling and raw_values[k] < line_v - tol:
                return False, [], 0, 0
        
        touches = [p1]
        for k in range(i + 1, j):
            p = pivots[k]
            line_v = slope * p["idx"] + intercept
            if abs(line_v) > 0 and abs(p["val"] - line_v) / abs(line_v) < 0.02:
                touches.append(p)
        touches.append(p2)
        
        if len(touches) < 3:
            return False, [], 0, 0
        
        return True, touches, slope, intercept
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        self._wedges = []
        
        highs = df["High"].values
        lows = df["Low"].values
        n = len(df)
        
        hp = self._find_pivots(df, "high")
        lp = self._find_pivots(df, "low")
        
        if len(hp) < 3 or len(lp) < 3:
            return df
        
        upper_lines = []
        for i in range(len(hp)):
            for j in range(i + 2, min(i + 8, len(hp))):
                span = hp[j]["idx"] - hp[i]["idx"]
                if span < self.min_span or span > self.max_span:
                    continue
                valid, touches, slope, intercept = self._validate_trendline(
                    highs, hp, i, j, is_ceiling=True)
                if valid:
                    upper_lines.append({
                        "p1": hp[i], "p2": hp[j],
                        "touches": touches,
                        "slope": slope, "intercept": intercept,
                    })
        
        lower_lines = []
        for i in range(len(lp)):
            for j in range(i + 2, min(i + 8, len(lp))):
                span = lp[j]["idx"] - lp[i]["idx"]
                if span < self.min_span * 0.5 or span > self.max_span:
                    continue
                valid, touches, slope, intercept = self._validate_trendline(
                    lows, lp, i, j, is_ceiling=False)
                if valid:
                    lower_lines.append({
                        "p1": lp[i], "p2": lp[j],
                        "touches": touches,
                        "slope": slope, "intercept": intercept,
                    })
        
        rejects = {"time": 0, "val": 0, "slope": 0, "conv": 0, "type": 0, "apex": 0}
        
        for upper in upper_lines:
            h1, h2 = upper["p1"], upper["p2"]
            
            for lower in lower_lines:
                l1, l2 = lower["p1"], lower["p2"]
                
                # Check time intersection instead of exact start/end match
                overlap_start = max(h1["idx"], l1["idx"])
                overlap_end = min(h2["idx"], l2["idx"])
                overlap = overlap_end - overlap_start
                max_span = max(h2["idx"] - h1["idx"], l2["idx"] - l1["idx"])
                
                if overlap < max_span * 0.5:
                    rejects["time"] += 1
                    continue
                
                # Check that lower line is below upper line in intersection zone
                h_at_start = upper["slope"] * overlap_start + upper["intercept"]
                l_at_start = lower["slope"] * overlap_start + lower["intercept"]
                h_at_end = upper["slope"] * overlap_end + upper["intercept"]
                l_at_end = lower["slope"] * overlap_end + lower["intercept"]
                
                if l_at_start >= h_at_start or l_at_end >= h_at_end:
                    rejects["val"] += 1
                    continue
                
                h_slope = upper["slope"]
                l_slope = lower["slope"]
                
                if h_slope >= l_slope:
                    rejects["slope"] += 1
                    continue
                
                w_start = h_at_start - l_at_start
                w_end = h_at_end - l_at_end
                if w_start <= 0 or w_end <= 0:
                    rejects["conv"] += 1
                    continue
                
                conv = (w_start - w_end) / w_start
                if conv < 0.15:
                    rejects["conv"] += 1
                    continue
                
                if h_slope > 0 and l_slope > 0:
                    wtype = "rising"
                elif h_slope < 0 and l_slope < 0:
                    wtype = "falling"
                else:
                    rejects["type"] += 1
                    continue
                
                h_int = upper["intercept"]
                l_int = lower["intercept"]
                if h_slope == l_slope:
                    rejects["slope"] += 1
                    continue
                ax = (l_int - h_int) / (h_slope - l_slope)
                ay = h_slope * ax + h_int
                
                pe = max(h2["idx"], l2["idx"])
                span = h2["idx"] - h1["idx"]
                if ax <= pe or ax - pe > span * 2:
                    rejects["apex"] += 1
                    continue
                
                apex_dist = ax - pe
                score = conv * (len(upper["touches"]) + len(lower["touches"])) / (1 + apex_dist / span)
                
                # Find breakout point — where close breaks the line
                closes = df["Close"].values
                pattern_start = min(h1["idx"], l1["idx"])
                breakout_idx = None
                for k in range(pattern_start + self.min_span, min(pe + 20, n)):
                    upper_v = h_slope * k + h_int
                    lower_v = l_slope * k + l_int
                    if closes[k] > upper_v * 1.015:
                        breakout_idx = k
                        break
                    if closes[k] < lower_v * 0.985:
                        breakout_idx = k
                        break
                
                # If breakout before pattern midpoint — not a wedge
                midpoint = (pattern_start + pe) // 2
                if breakout_idx and breakout_idx < midpoint:
                    continue
                
                # Determine drawing end
                if breakout_idx and breakout_idx < pe:
                    draw_end = breakout_idx
                else:
                    draw_end = pe
                
                already = any(abs(w["h1"]["idx"] - h1["idx"]) < 30 for w in self._wedges)
                if already:
                    continue
                
                self._wedges.append({
                    "type": wtype,
                    "h1": h1, "h2": h2, "l1": l1, "l2": l2,
                    "h_touches": upper["touches"],
                    "l_touches": lower["touches"],
                    "apex_x": ax, "apex_y": ay,
                    "conv": conv, "score": score,
                    "h_slope": h_slope, "h_int": h_int,
                    "l_slope": l_slope, "l_int": l_int,
                    "draw_end": draw_end,
                    "draw_end_date": df.index[draw_end],
                    "breakout": breakout_idx is not None and breakout_idx <= pe,
                })
        
        self._wedges.sort(key=lambda x: -x["score"])
        
        return df
    
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        if not self._wedges:
            return fig
        
        display_start = data.index[0]
        display_end = data.index[-1]
        n = len(data)
        dates = data.index
        
        visible = [w for w in self._wedges
                   if w["h1"]["date"] >= display_start and w["h2"]["date"] <= display_end]
        
        if not visible:
            return fig
        
        shown_r = False
        shown_f = False
        
        for wedge in visible[:1]:
            color = "#FFA726" if wedge["type"] == "rising" else "#42A5F5"
            
            if wedge["type"] == "rising":
                name = "Rising Wedge" if not shown_r else None
                shown_r = True
            else:
                name = "Falling Wedge" if not shown_f else None
                shown_f = True
            
            h1, l1 = wedge["h1"], wedge["l1"]
            h_slope = wedge["h_slope"]
            h_int = wedge["h_int"]
            l_slope = wedge["l_slope"]
            l_int = wedge["l_int"]
            
            draw_end = wedge["draw_end"]
            draw_end_date = wedge["draw_end_date"]
            
            h_end_val = h_slope * draw_end + h_int
            l_end_val = l_slope * draw_end + l_int
            
            # Upper trendline (h1 → draw_end)
            fig.add_trace(go.Scatter(
                x=[h1["date"], draw_end_date],
                y=[h1["val"], h_end_val],
                mode="lines", line=dict(color=color, width=2),
                name=name, showlegend=name is not None,
            ), row=row, col=1)
            
            # Lower trendline (l1 → draw_end)
            fig.add_trace(go.Scatter(
                x=[l1["date"], draw_end_date],
                y=[l1["val"], l_end_val],
                mode="lines", line=dict(color=color, width=2),
                showlegend=False,
            ), row=row, col=1)
            
            # If no breakout — show short dashed line with convergence direction
            if not wedge["breakout"]:
                ext_bars = 15
                ext_end = draw_end + ext_bars
                h_ext_val = h_slope * ext_end + h_int
                l_ext_val = l_slope * ext_end + l_int
                
                # Find nearest date in display_df
                draw_end_pos = data.index.get_indexer([draw_end_date], method="nearest")[0]
                ext_pos = min(draw_end_pos + ext_bars, n - 1)
                ext_date = dates[ext_pos]
                
                fig.add_trace(go.Scatter(
                    x=[draw_end_date, ext_date],
                    y=[h_end_val, h_ext_val],
                    mode="lines", line=dict(color=color, width=1.5, dash="dash"),
                    showlegend=False,
                ), row=row, col=1)
                
                fig.add_trace(go.Scatter(
                    x=[draw_end_date, ext_date],
                    y=[l_end_val, l_ext_val],
                    mode="lines", line=dict(color=color, width=1.5, dash="dash"),
                    showlegend=False,
                ), row=row, col=1)
            
            # Touch points (only those up to draw_end)
            h_visible = [p for p in wedge["h_touches"] if p["idx"] <= draw_end]
            l_visible = [p for p in wedge["l_touches"] if p["idx"] <= draw_end]
            
            if h_visible:
                fig.add_trace(go.Scatter(
                    x=[p["date"] for p in h_visible],
                    y=[p["val"] for p in h_visible],
                    mode="markers", marker=dict(size=8, color=color, symbol="circle"),
                    showlegend=False,
                ), row=row, col=1)
            
            if l_visible:
                fig.add_trace(go.Scatter(
                    x=[p["date"] for p in l_visible],
                    y=[p["val"] for p in l_visible],
                    mode="markers", marker=dict(size=8, color=color, symbol="circle"),
                    showlegend=False,
                ), row=row, col=1)
            
            # Breakout marker
            if wedge["breakout"]:
                bo_date = draw_end_date
                bo_val = h_end_val if h_slope > 0 else l_end_val
                fig.add_trace(go.Scatter(
                    x=[bo_date], y=[bo_val],
                    mode="markers", marker=dict(size=12, color=color, symbol="x", 
                                                 line=dict(width=2, color=color)),
                    showlegend=False, hovertemplate="Breakout<extra></extra>",
                ), row=row, col=1)
        
        return fig
