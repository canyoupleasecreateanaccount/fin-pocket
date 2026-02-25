import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


class Pennant(BaseSignal):
    """
    Detects bullish and bearish flags and pennants.

    Flag:
      Flagpole (sharp move) + correction in a PARALLEL channel AGAINST the trend.
      Bull Flag: flagpole up → correction down in parallel channel
      Bear Flag: flagpole down → correction up in parallel channel

    Pennant:
      Flagpole + correction in a CONVERGING triangle.
      Similar to a flag, but lines converge.
    """

    def __init__(
        self,
        lookback: int = 5,
        min_pole_bars: int = 3,
        max_pole_bars: int = 7,
        min_pole_move_pct: float = 5.0,
        min_body_bars: int = 7,
        max_body_bars: int = 35,
        max_retrace_pct: float = 0.50,
    ):
        self.lookback = lookback
        self.min_pole_bars = min_pole_bars
        self.max_pole_bars = max_pole_bars
        self.min_pole_move_pct = min_pole_move_pct
        self.min_body_bars = min_body_bars
        self.max_body_bars = max_body_bars
        self.max_retrace_pct = max_retrace_pct
        self._patterns = []

    @property
    def name(self) -> str:
        return "Flag & Pennant"

    def _find_swing_points(self, values: np.ndarray, lb: int, kind: str) -> list[int]:
        pts = []
        for i in range(lb, len(values) - lb):
            window = values[i - lb : i + lb + 1]
            if kind == "high" and values[i] == window.max():
                pts.append(i)
            elif kind == "low" and values[i] == window.min():
                pts.append(i)
        return pts

    def _find_flagpole_bull(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, peak_idx: int
    ) -> dict | None:
        """Searches for a bullish flagpole ending at peak_idx (swing high)."""
        best = None

        for length in range(self.min_pole_bars, min(self.max_pole_bars, peak_idx) + 1):
            start_idx = peak_idx - length
            if start_idx < 0:
                continue

            low_in_pole = float(np.min(lows[start_idx : start_idx + max(1, length // 3) + 1]))
            high_at_peak = float(highs[peak_idx])
            move_pct = (high_at_peak - low_in_pole) / low_in_pole * 100

            if move_pct < self.min_pole_move_pct:
                continue

            segment = closes[start_idx : peak_idx + 1]
            third = max(1, len(segment) // 3)
            if np.mean(segment[:third]) > np.mean(segment[-third:]):
                continue

            if best is None or move_pct > best["move_pct"]:
                best = {
                    "start_idx": start_idx,
                    "end_idx": peak_idx,
                    "start_price": low_in_pole,
                    "end_price": high_at_peak,
                    "move_pct": move_pct,
                }

        return best

    def _find_flagpole_bear(
        self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, trough_idx: int
    ) -> dict | None:
        """Searches for a bearish flagpole ending at trough_idx (swing low)."""
        best = None

        for length in range(self.min_pole_bars, min(self.max_pole_bars, trough_idx) + 1):
            start_idx = trough_idx - length
            if start_idx < 0:
                continue

            high_in_pole = float(np.max(highs[start_idx : start_idx + max(1, length // 3) + 1]))
            low_at_trough = float(lows[trough_idx])
            move_pct = (high_in_pole - low_at_trough) / high_in_pole * 100

            if move_pct < self.min_pole_move_pct:
                continue

            segment = closes[start_idx : trough_idx + 1]
            third = max(1, len(segment) // 3)
            if np.mean(segment[:third]) < np.mean(segment[-third:]):
                continue

            if best is None or move_pct > best["move_pct"]:
                best = {
                    "start_idx": start_idx,
                    "end_idx": trough_idx,
                    "start_price": high_in_pole,
                    "end_price": low_at_trough,
                    "move_pct": move_pct,
                }

        return best

    def _validate_body(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        start: int,
        end: int,
        direction: str,
        pole_move: float,
        pole_start_price: float,
        pole_end_price: float,
        pole_length: int,
    ) -> dict | None:
        """
        Validates the correction start..end for flag or pennant pattern.

        Flag: parallel channel AGAINST the trend.
        Pennant: converging triangle.

        Key requirements:
        - Body shorter or ≈ flagpole length
        - Channel narrow (< 50% of flagpole height)
        - Correction goes AGAINST the trend
        - Retracement moderate (not > max_retrace_pct)
        """
        span = end - start + 1
        if span < self.min_body_bars:
            return None

        if span > pole_length * 2:
            return None

        x = np.arange(span, dtype=float)
        h_vals = highs[start : end + 1].astype(float)
        l_vals = lows[start : end + 1].astype(float)

        h_slope, h_int = np.polyfit(x, h_vals, 1)
        l_slope, l_int = np.polyfit(x, l_vals, 1)

        pole_height = abs(pole_end_price - pole_start_price)
        avg_channel_width = np.mean(h_vals - l_vals)
        if avg_channel_width > pole_height * 0.50:
            return None

        avg_slope = (h_slope + l_slope) / 2

        if direction == "bull":
            if avg_slope > 0:
                return None

            retrace = abs(pole_end_price - np.min(l_vals)) / pole_height
            if retrace > self.max_retrace_pct or retrace < 0.08:
                return None
        else:
            if avg_slope < 0:
                return None

            retrace = abs(np.max(h_vals) - pole_end_price) / pole_height
            if retrace > self.max_retrace_pct or retrace < 0.08:
                return None

        width_start = h_int - l_int
        width_end = (h_slope * (span - 1) + h_int) - (l_slope * (span - 1) + l_int)

        if width_start <= 0 or width_end <= 0:
            return None

        width_ratio = min(width_start, width_end) / max(width_start, width_end)

        if width_ratio > 0.65:
            form = "flag"
        elif (width_start - width_end) / width_start > 0.15:
            form = "pennant"
        else:
            return None

        h_fitted = h_slope * x + h_int
        h_shift = np.max(h_vals - h_fitted)
        if h_shift < 0:
            h_shift = 0
        h_int_adj = h_int + h_shift

        l_fitted = l_slope * x + l_int
        l_shift = np.min(l_vals - l_fitted)
        if l_shift > 0:
            l_shift = 0
        l_int_adj = l_int + l_shift

        h_start_val = float(h_int_adj)
        h_end_val = float(h_slope * (span - 1) + h_int_adj)
        l_start_val = float(l_int_adj)
        l_end_val = float(l_slope * (span - 1) + l_int_adj)

        return {
            "form": form,
            "h_start_val": h_start_val,
            "h_end_val": h_end_val,
            "l_start_val": l_start_val,
            "l_end_val": l_end_val,
            "h_slope": float(h_slope),
            "l_slope": float(l_slope),
            "width_ratio": width_ratio,
            "retrace": retrace,
            "span": span,
        }

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        self._patterns = []

        closes = df["Close"].values
        highs = df["High"].values
        lows = df["Low"].values
        n = len(df)
        dates = df.index

        swing_highs = self._find_swing_points(highs, self.lookback, "high")
        swing_lows = self._find_swing_points(lows, self.lookback, "low")

        used_zones: list[tuple[int, int]] = []

        def overlaps(s, e):
            for us, ue in used_zones:
                if s <= ue and e >= us:
                    return True
            return False

        candidates = []

        for sh_idx in swing_highs:
            pole = self._find_flagpole_bull(highs, lows, closes, sh_idx)
            if not pole:
                continue

            best_body = None
            best_end = None

            for p_end in range(
                sh_idx + self.min_body_bars,
                min(sh_idx + self.max_body_bars + 1, n),
            ):
                pole_len = pole["end_idx"] - pole["start_idx"]
                body = self._validate_body(
                    highs, lows, closes, sh_idx, p_end, "bull",
                    pole["move_pct"], pole["start_price"], pole["end_price"],
                    pole_len,
                )
                if body:
                    score = pole["move_pct"] * (1 - body["retrace"]) * body["width_ratio"]
                    if best_body is None or score > best_body["_score"]:
                        body["_score"] = score
                        best_body = body
                        best_end = p_end

            if best_body is None:
                continue

            candidates.append({
                "type": "bull",
                "pole": pole,
                "body": best_body,
                "body_end": best_end,
                "sh_idx": sh_idx,
                "score": best_body["_score"],
            })

        for sl_idx in swing_lows:
            pole = self._find_flagpole_bear(highs, lows, closes, sl_idx)
            if not pole:
                continue

            best_body = None
            best_end = None

            for p_end in range(
                sl_idx + self.min_body_bars,
                min(sl_idx + self.max_body_bars + 1, n),
            ):
                pole_len = pole["end_idx"] - pole["start_idx"]
                body = self._validate_body(
                    highs, lows, closes, sl_idx, p_end, "bear",
                    pole["move_pct"], pole["start_price"], pole["end_price"],
                    pole_len,
                )
                if body:
                    score = pole["move_pct"] * (1 - body["retrace"]) * body["width_ratio"]
                    if best_body is None or score > best_body["_score"]:
                        body["_score"] = score
                        best_body = body
                        best_end = p_end

            if best_body is None:
                continue

            candidates.append({
                "type": "bear",
                "pole": pole,
                "body": best_body,
                "body_end": best_end,
                "sh_idx": sl_idx,
                "score": best_body["_score"],
            })

        candidates.sort(key=lambda x: -x["score"])

        for c in candidates:
            pole = c["pole"]
            zone_start = pole["start_idx"]
            zone_end = c["body_end"]

            if overlaps(zone_start, zone_end):
                continue

            used_zones.append((zone_start, zone_end))
            body = c["body"]
            del body["_score"]

            self._patterns.append({
                "type": c["type"],
                "form": body["form"],
                "pole_start_date": dates[pole["start_idx"]],
                "pole_end_date": dates[pole["end_idx"]],
                "pole_start_price": pole["start_price"],
                "pole_end_price": pole["end_price"],
                "pole_move_pct": pole["move_pct"],
                "body_start_date": dates[c["sh_idx"]],
                "body_end_date": dates[c["body_end"]],
                "body": body,
                "score": c["score"],
            })

        print(f"[Flag/Pennant] Found {len(self._patterns)} patterns:")
        for p in self._patterns:
            label = "Flag" if p["form"] == "flag" else "Pennant"
            print(
                f"  {p['type']} {label}: {p['pole_start_date'].strftime('%Y-%m-%d')} → "
                f"{p['body_end_date'].strftime('%Y-%m-%d')}, "
                f"pole={p['pole_move_pct']:.1f}%, retrace={p['body']['retrace']:.0%}, "
                f"width_ratio={p['body']['width_ratio']:.0%}"
            )

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        if not self._patterns:
            return fig

        display_start = data.index[0]
        display_end = data.index[-1]

        visible = [
            p
            for p in self._patterns
            if p["pole_start_date"] >= display_start
            and p["body_end_date"] <= display_end
        ]

        if not visible:
            return fig

        legend_shown = set()

        for pat in visible[:6]:
            is_bull = pat["type"] == "bull"
            is_flag = pat["form"] == "flag"
            color = "#26A69A" if is_bull else "#EF5350"

            if is_bull and is_flag:
                label = "Bull Flag"
            elif is_bull:
                label = "Bull Pennant"
            elif is_flag:
                label = "Bear Flag"
            else:
                label = "Bear Pennant"

            show_legend = label not in legend_shown
            if show_legend:
                legend_shown.add(label)

            body = pat["body"]

            # Flagpole (dashed)
            fig.add_trace(
                go.Scatter(
                    x=[pat["pole_start_date"], pat["pole_end_date"]],
                    y=[pat["pole_start_price"], pat["pole_end_price"]],
                    mode="lines",
                    line=dict(color=color, width=2, dash="dot"),
                    name=label if show_legend else None,
                    showlegend=show_legend,
                    hovertemplate=(
                        f"{label}<br>"
                        f"Pole: {pat['pole_move_pct']:.1f}%<br>"
                        f"Retrace: {body['retrace']:.0%}<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )

            # Upper line of channel/triangle
            fig.add_trace(
                go.Scatter(
                    x=[pat["body_start_date"], pat["body_end_date"]],
                    y=[body["h_start_val"], body["h_end_val"]],
                    mode="lines",
                    line=dict(color=color, width=2),
                    showlegend=False,
                ),
                row=row,
                col=1,
            )

            # Lower line of channel/triangle
            fig.add_trace(
                go.Scatter(
                    x=[pat["body_start_date"], pat["body_end_date"]],
                    y=[body["l_start_val"], body["l_end_val"]],
                    mode="lines",
                    line=dict(color=color, width=2),
                    showlegend=False,
                ),
                row=row,
                col=1,
            )

        return fig
