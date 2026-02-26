import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


class DoubleTopBottom(BaseSignal):
    """
    Detects Double Top and Double Bottom reversal patterns.

    Double Top (bearish):
        Two peaks at roughly the same price level separated by a valley (neckline).
        Confirmed when price breaks below the neckline.

    Double Bottom (bullish):
        Two troughs at roughly the same price level separated by a peak (neckline).
        Confirmed when price breaks above the neckline.
    """

    def __init__(
        self,
        lookback: int = 8,
        tolerance_pct: float = 2.0,
        min_distance: int = 15,
        max_distance: int = 120,
        min_depth_pct: float = 3.0,
        recent_bars: int = 300,
    ):
        """
        Args:
            lookback: Bars on each side to confirm a swing point
            tolerance_pct: Max % difference between the two peaks/troughs
            min_distance: Min bars between the two peaks/troughs
            max_distance: Max bars between the two peaks/troughs
            min_depth_pct: Min % depth of the valley/peak between the two extremes
            recent_bars: Only scan the last N bars
        """
        self.lookback = lookback
        self.tolerance_pct = tolerance_pct
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.min_depth_pct = min_depth_pct
        self.recent_bars = recent_bars
        self._patterns: list[dict] = []

    @property
    def name(self) -> str:
        return "Double Top/Bottom"

    def _find_swing_points(
        self, values: np.ndarray, kind: str
    ) -> list[tuple[int, float]]:
        pts: list[tuple[int, float]] = []
        lb = self.lookback
        for i in range(lb, len(values) - lb):
            window = values[i - lb : i + lb + 1]
            if kind == "high" and values[i] == window.max():
                pts.append((i, float(values[i])))
            elif kind == "low" and values[i] == window.min():
                pts.append((i, float(values[i])))
        return pts

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        self._patterns = []

        n = len(df)
        if n < self.min_distance + self.lookback * 2:
            return df

        start = max(0, n - self.recent_bars)
        highs = df["High"].values
        lows = df["Low"].values
        closes = df["Close"].values
        dates = df.index

        swing_highs = self._find_swing_points(highs[start:], "high")
        swing_lows = self._find_swing_points(lows[start:], "low")

        # Shift indices back to full DataFrame space
        swing_highs = [(i + start, v) for i, v in swing_highs]
        swing_lows = [(i + start, v) for i, v in swing_lows]

        used_zones: list[tuple[int, int]] = []

        def overlaps(s: int, e: int) -> bool:
            for us, ue in used_zones:
                if s <= ue and e >= us:
                    return True
            return False

        candidates: list[dict] = []

        # --- Double Tops ---
        for i in range(len(swing_highs)):
            for j in range(i + 1, len(swing_highs)):
                idx1, val1 = swing_highs[i]
                idx2, val2 = swing_highs[j]
                dist = idx2 - idx1

                if dist < self.min_distance or dist > self.max_distance:
                    continue

                avg_peak = (val1 + val2) / 2
                if avg_peak == 0:
                    continue
                diff_pct = abs(val1 - val2) / avg_peak * 100
                if diff_pct > self.tolerance_pct:
                    continue

                valley_low = float(np.min(lows[idx1:idx2 + 1]))
                depth_pct = (avg_peak - valley_low) / avg_peak * 100
                if depth_pct < self.min_depth_pct:
                    continue

                neckline = valley_low

                confirmed = False
                confirm_idx = None
                for k in range(idx2 + 1, min(idx2 + dist, n)):
                    if closes[k] < neckline * 0.995:
                        confirmed = True
                        confirm_idx = k
                        break

                score = depth_pct * (1 + int(confirmed))

                candidates.append({
                    "type": "double_top",
                    "idx1": idx1, "val1": val1,
                    "idx2": idx2, "val2": val2,
                    "neckline": neckline,
                    "depth_pct": depth_pct,
                    "confirmed": confirmed,
                    "confirm_idx": confirm_idx,
                    "score": score,
                })

        # --- Double Bottoms ---
        for i in range(len(swing_lows)):
            for j in range(i + 1, len(swing_lows)):
                idx1, val1 = swing_lows[i]
                idx2, val2 = swing_lows[j]
                dist = idx2 - idx1

                if dist < self.min_distance or dist > self.max_distance:
                    continue

                avg_trough = (val1 + val2) / 2
                if avg_trough == 0:
                    continue
                diff_pct = abs(val1 - val2) / avg_trough * 100
                if diff_pct > self.tolerance_pct:
                    continue

                peak_high = float(np.max(highs[idx1:idx2 + 1]))
                depth_pct = (peak_high - avg_trough) / avg_trough * 100
                if depth_pct < self.min_depth_pct:
                    continue

                neckline = peak_high

                confirmed = False
                confirm_idx = None
                for k in range(idx2 + 1, min(idx2 + dist, n)):
                    if closes[k] > neckline * 1.005:
                        confirmed = True
                        confirm_idx = k
                        break

                score = depth_pct * (1 + int(confirmed))

                candidates.append({
                    "type": "double_bottom",
                    "idx1": idx1, "val1": val1,
                    "idx2": idx2, "val2": val2,
                    "neckline": neckline,
                    "depth_pct": depth_pct,
                    "confirmed": confirmed,
                    "confirm_idx": confirm_idx,
                    "score": score,
                })

        candidates.sort(key=lambda x: -x["score"])

        for c in candidates:
            zone_start = c["idx1"]
            zone_end = c["confirm_idx"] or c["idx2"]
            if overlaps(zone_start, zone_end):
                continue
            used_zones.append((zone_start, zone_end))

            c["date1"] = dates[c["idx1"]]
            c["date2"] = dates[c["idx2"]]
            c["confirm_date"] = dates[c["confirm_idx"]] if c["confirm_idx"] else None

            self._patterns.append(c)

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        if not self._patterns:
            return fig

        display_start = data.index[0]
        display_end = data.index[-1]

        visible = [
            p for p in self._patterns
            if p["date1"] >= display_start and p["date2"] <= display_end
        ]

        if not visible:
            return fig

        legend_shown = {"double_top": False, "double_bottom": False}

        for pat in visible[:4]:
            is_top = pat["type"] == "double_top"
            color = "#EF5350" if is_top else "#26A69A"
            label = "Double Top" if is_top else "Double Bottom"

            show_legend = not legend_shown[pat["type"]]
            if show_legend:
                legend_shown[pat["type"]] = True

            # Two peaks/troughs markers
            fig.add_trace(
                go.Scatter(
                    x=[pat["date1"], pat["date2"]],
                    y=[pat["val1"], pat["val2"]],
                    mode="markers+lines",
                    marker=dict(size=10, color=color, symbol="diamond",
                                line=dict(color="#fff", width=1)),
                    line=dict(color=color, width=1.5, dash="dot"),
                    name=label if show_legend else None,
                    showlegend=show_legend,
                    hovertemplate=(
                        f"{label}<br>"
                        f"Depth: {pat['depth_pct']:.1f}%<br>"
                        f"{'Confirmed' if pat['confirmed'] else 'Pending'}"
                        "<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )

            # Neckline
            neckline_end = pat["confirm_date"] or pat["date2"]
            fig.add_trace(
                go.Scatter(
                    x=[pat["date1"], neckline_end],
                    y=[pat["neckline"], pat["neckline"]],
                    mode="lines",
                    line=dict(color=color, width=1.5, dash="dash"),
                    showlegend=False,
                ),
                row=row,
                col=1,
            )

            # Confirmation marker
            if pat["confirmed"] and pat["confirm_date"]:
                confirm_price = data.loc[pat["confirm_date"], "Close"] if pat["confirm_date"] in data.index else pat["neckline"]
                marker_symbol = "triangle-down" if is_top else "triangle-up"
                fig.add_trace(
                    go.Scatter(
                        x=[pat["confirm_date"]],
                        y=[confirm_price],
                        mode="markers",
                        marker=dict(size=14, color=color, symbol=marker_symbol,
                                    line=dict(color="#fff", width=1.5)),
                        showlegend=False,
                        hovertemplate=f"{label} Breakout<extra></extra>",
                    ),
                    row=row,
                    col=1,
                )

        return fig
