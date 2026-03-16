import pandas as pd
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
        Finds the most significant swing high and swing low pair
        within recent_bars, preferring the pair with the largest price range.
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

        best_pair = None
        best_range = 0

        for sh in swing_highs:
            for sl in swing_lows:
                if sh[0] == sl[0]:
                    continue
                price_range = sh[1] - sl[1]
                if price_range <= 0:
                    continue
                move_pct = price_range / sl[1] * 100 if sl[1] != 0 else 0
                if move_pct < self.min_move_pct:
                    continue
                if price_range > best_range:
                    best_range = price_range
                    if sh[0] > sl[0]:
                        best_pair = (
                            {"price": sl[1], "date": sl[2], "idx": sl[0]},
                            {"price": sh[1], "date": sh[2], "idx": sh[0]},
                            "up",
                        )
                    else:
                        best_pair = (
                            {"price": sh[1], "date": sh[2], "idx": sh[0]},
                            {"price": sl[1], "date": sl[2], "idx": sl[0]},
                            "down",
                        )

        if best_pair:
            return best_pair
        return None, None, None

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        swing_a, swing_b, direction = self._find_major_swings(df)

        if swing_a is None:
            self._levels = []
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

        return df

    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        if not self._levels:
            return fig

        x_end = data.index[-1]

        earlier_swing_date = None
        if self._swing_low and self._swing_high:
            sh_date = self._swing_high["date"]
            sl_date = self._swing_low["date"]
            earlier_swing_date = min(sh_date, sl_date)

        x_line_start = earlier_swing_date if earlier_swing_date is not None else data.index[max(0, len(data) - len(data) // 4)]

        prev_price = None
        prev_color = None
        for lv in self._levels:
            fib = lv["fib"]
            price = lv["price"]
            color = FIB_COLORS.get(fib, "rgba(255,255,255,0.5)")

            fig.add_trace(
                go.Scatter(
                    x=[x_line_start, x_end],
                    y=[price, price],
                    mode="lines",
                    line=dict(color=color, width=1, dash="dash"),
                    name=f"Fib {fib:.1%}",
                    showlegend=False,
                    hovertemplate=f"Fib {fib:.1%}: {price:.2f}<extra></extra>",
                ),
                row=row,
                col=1,
            )

            if prev_price is not None:
                fill_color = prev_color.replace("0.7)", "0.07)")
                fig.add_trace(
                    go.Scatter(
                        x=[x_line_start, x_end, x_end, x_line_start, x_line_start],
                        y=[prev_price, prev_price, price, price, prev_price],
                        fill="toself",
                        fillcolor=fill_color,
                        line=dict(width=0),
                        mode="lines",
                        showlegend=False,
                        hoverinfo="skip",
                    ),
                    row=row,
                    col=1,
                )

            fig.add_annotation(
                x=x_end,
                y=price,
                text=f"Fib {fib:.1%}: {price:.2f}",
                showarrow=False,
                xanchor="left",
                font=dict(color=color, size=9),
                xshift=5,
                row=row,
                col=1,
            )

            prev_price = price
            prev_color = color

        if self._swing_low and self._swing_high:
            sh_date = self._swing_high["date"]
            sl_date = self._swing_low["date"]

            fig.add_trace(
                go.Scatter(
                    x=[sh_date, sl_date],
                    y=[self._swing_high["price"], self._swing_low["price"]],
                    mode="lines+markers",
                    line=dict(color="rgba(255, 255, 255, 0.5)", width=1.5, dash="dot"),
                    marker=dict(size=9, symbol="diamond",
                                color=["#F44336", "#4CAF50"]),
                    name="Fib Swing",
                    showlegend=True,
                    hovertemplate=[
                        f"Swing High: {self._swing_high['price']:.2f}<extra></extra>",
                        f"Swing Low: {self._swing_low['price']:.2f}<extra></extra>",
                    ],
                ),
                row=row,
                col=1,
            )

        return fig
