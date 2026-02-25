import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .base import BaseSignal


FIB_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

FIB_COLORS = {
    0.0: "rgba(244, 67, 54, 0.7)",
    0.236: "rgba(255, 152, 0, 0.7)",
    0.382: "rgba(255, 235, 59, 0.7)",
    0.5: "rgba(76, 175, 80, 0.7)",
    0.618: "rgba(33, 150, 243, 0.7)",
    0.786: "rgba(156, 39, 176, 0.7)",
    1.0: "rgba(244, 67, 54, 0.7)",
}


class Fibonacci(BaseSignal):
    """
    Fibonacci Retracement levels.

    Identifies the last significant move (swing high → swing low or vice versa)
    and draws retracement levels between them: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%.
    """

    def __init__(
        self,
        lookback: int = 10,
        min_move_pct: float = 8.0,
        recent_bars: int = 200,
    ):
        self.lookback = lookback
        self.min_move_pct = min_move_pct
        self.recent_bars = recent_bars
        self._swing_high = None
        self._swing_low = None
        self._direction = None
        self._levels = []

    @property
    def name(self) -> str:
        return "Fibonacci"

    def _find_major_swings(self, data: pd.DataFrame):
        """
        Finds the last significant swing high and swing low
        within recent_bars.
        """
        recent = data.tail(self.recent_bars) if len(data) > self.recent_bars else data
        highs = recent["High"].values
        lows = recent["Low"].values
        dates = recent.index
        n = len(recent)
        lb = self.lookback

        swing_highs = []
        swing_lows = []

        for i in range(lb, n - lb):
            window_h = highs[i - lb : i + lb + 1]
            if highs[i] == window_h.max():
                swing_highs.append((i, float(highs[i]), dates[i]))

            window_l = lows[i - lb : i + lb + 1]
            if lows[i] == window_l.min():
                swing_lows.append((i, float(lows[i]), dates[i]))

        if not swing_highs or not swing_lows:
            return None, None, None

        last_sh = swing_highs[-1]
        last_sl = swing_lows[-1]

        if last_sh[0] > last_sl[0]:
            move_pct = (last_sh[1] - last_sl[1]) / last_sl[1] * 100 if last_sl[1] != 0 else 0
            if move_pct >= self.min_move_pct:
                return (
                    {"price": last_sl[1], "date": last_sl[2], "idx": last_sl[0]},
                    {"price": last_sh[1], "date": last_sh[2], "idx": last_sh[0]},
                    "up",
                )
        else:
            move_pct = (last_sh[1] - last_sl[1]) / last_sl[1] * 100 if last_sl[1] != 0 else 0
            if move_pct >= self.min_move_pct:
                return (
                    {"price": last_sh[1], "date": last_sh[2], "idx": last_sh[0]},
                    {"price": last_sl[1], "date": last_sl[2], "idx": last_sl[0]},
                    "down",
                )

        best_sh = max(swing_highs, key=lambda x: x[1])
        best_sl = min(swing_lows, key=lambda x: x[1])
        move_pct = (best_sh[1] - best_sl[1]) / best_sl[1] * 100 if best_sl[1] != 0 else 0

        if move_pct < self.min_move_pct:
            return None, None, None

        if best_sh[0] > best_sl[0]:
            return (
                {"price": best_sl[1], "date": best_sl[2], "idx": best_sl[0]},
                {"price": best_sh[1], "date": best_sh[2], "idx": best_sh[0]},
                "up",
            )
        else:
            return (
                {"price": best_sh[1], "date": best_sh[2], "idx": best_sh[0]},
                {"price": best_sl[1], "date": best_sl[2], "idx": best_sl[0]},
                "down",
            )

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        swing_a, swing_b, direction = self._find_major_swings(df)

        if swing_a is None:
            self._levels = []
            print("[Fibonacci] No significant move found for Fibonacci levels")
            return df

        self._direction = direction

        if direction == "up":
            self._swing_low = swing_a
            self._swing_high = swing_b
            low_price = swing_a["price"]
            high_price = swing_b["price"]
        else:
            self._swing_high = swing_a
            self._swing_low = swing_b
            low_price = swing_b["price"]
            high_price = swing_a["price"]

        diff = high_price - low_price

        self._levels = []
        for fib in FIB_LEVELS:
            price = high_price - diff * fib
            self._levels.append({
                "fib": fib,
                "price": price,
            })

        move_display = diff / low_price * 100 if low_price != 0 else 0
        print(f"[Fibonacci] Move {direction}: "
              f"{low_price:.2f} → {high_price:.2f} ({move_display:.1f}%)")
        for lv in self._levels:
            print(f"  {lv['fib']:.1%}: {lv['price']:.2f}")

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        if not self._levels:
            return fig

        x_start = data.index[0]
        x_end = data.index[-1]

        for lv in self._levels:
            fib = lv["fib"]
            price = lv["price"]
            color = FIB_COLORS.get(fib, "rgba(255,255,255,0.5)")

            fig.add_hline(
                y=price,
                line_dash="dash",
                line_color=color,
                line_width=1,
                annotation_text=f"Fib {fib:.1%}: {price:.2f}",
                annotation_position="right",
                annotation_font_color=color,
                annotation_font_size=9,
                row=row,
                col=1,
            )

        if self._swing_low and self._swing_high:
            sh_date = self._swing_high["date"]
            sl_date = self._swing_low["date"]

            if sh_date >= x_start and sh_date <= x_end:
                fig.add_trace(
                    go.Scatter(
                        x=[sh_date],
                        y=[self._swing_high["price"]],
                        mode="markers",
                        marker=dict(size=8, color="#F44336", symbol="diamond"),
                        name="Fib Swing",
                        showlegend=True,
                        hovertemplate=f"Swing High: {self._swing_high['price']:.2f}<extra></extra>",
                    ),
                    row=row,
                    col=1,
                )

            if sl_date >= x_start and sl_date <= x_end:
                fig.add_trace(
                    go.Scatter(
                        x=[sl_date],
                        y=[self._swing_low["price"]],
                        mode="markers",
                        marker=dict(size=8, color="#4CAF50", symbol="diamond"),
                        name=None,
                        showlegend=False,
                        hovertemplate=f"Swing Low: {self._swing_low['price']:.2f}<extra></extra>",
                    ),
                    row=row,
                    col=1,
                )

        return fig
