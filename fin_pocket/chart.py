import logging

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from fin_pocket.signals.base import BaseSignal

logger = logging.getLogger(__name__)


class Chart:
    """Class for building charts with signals."""
    
    def __init__(self, data: pd.DataFrame, ticker: str = "", display_days: int | None = None, height: int = 1000):
        """
        Args:
            data: DataFrame with OHLCV data
            ticker: Ticker name
            display_days: Number of days to display (None = all data)
            height: Chart height in pixels
        """
        self.data = data
        self.ticker = ticker
        self.display_days = display_days
        self.height = height
        self.signals: list[BaseSignal] = []
        self._processed_data: pd.DataFrame | None = None
    
    def add_signal(self, signal: BaseSignal) -> "Chart":
        """Adds a signal to the chart."""
        self.signals.append(signal)
        return self
    
    def _process_signals(self) -> pd.DataFrame:
        """Applies all signals to the data."""
        df = self.data.copy()
        
        for signal in self.signals:
            try:
                df = signal.calculate(df)
            except Exception as exc:
                logger.warning("signal '%s' failed: %s", signal.name, exc)
        
        self._processed_data = df
        return df
    
    def build(self) -> go.Figure:
        """Creates the final chart."""
        df = self._process_signals()
        
        if self.display_days:
            display_df = df.tail(self.display_days)
        else:
            display_df = df
        
        separate_signals = [s for s in self.signals if s.panel == "separate"]
        main_signals = [s for s in self.signals if s.panel == "main"]
        
        num_rows = 2 + len(separate_signals)
        
        main_weight = 0.45
        sep_weight = 0.08
        vol_weight = 0.08
        total = main_weight + sep_weight * len(separate_signals) + vol_weight

        row_heights = [main_weight / total]
        for _ in separate_signals:
            row_heights.append(sep_weight / total)
        row_heights.append(vol_weight / total)
        
        fig = make_subplots(
            rows=num_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
        )
        
        fig.add_trace(
            go.Candlestick(
                x=display_df.index,
                open=display_df["Open"],
                high=display_df["High"],
                low=display_df["Low"],
                close=display_df["Close"],
                name="Price",
                increasing_line_color="#26A69A",
                decreasing_line_color="#EF5350",
            ),
            row=1,
            col=1,
        )
        
        last_close = display_df["Close"].iloc[-1]
        close_color = "#26A69A" if last_close >= display_df["Open"].iloc[-1] else "#EF5350"
        fig.add_annotation(
            x=display_df.index[-1], y=last_close,
            text=f" {last_close:.2f}",
            showarrow=False, xanchor="left", xshift=100,
            font=dict(color=close_color, size=10, family="monospace"),
            row=1, col=1,
        )

        for signal in main_signals:
            signal.plot(fig, display_df, row=1)
        
        for i, signal in enumerate(separate_signals):
            signal.plot(fig, display_df, row=2 + i)
        
        colors = ["#26A69A" if c >= o else "#EF5350" 
                  for c, o in zip(display_df["Close"], display_df["Open"])]
        
        volume_row = num_rows
        fig.add_trace(
            go.Bar(
                x=display_df.index,
                y=display_df["Volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.7,
            ),
            row=volume_row,
            col=1,
        )
        
        fig.update_layout(
            title=f"{self.ticker} Chart" if self.ticker else "Stock Chart",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=self.height,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            hovermode="x unified",
            dragmode="zoom",
        )
        
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
            ]
        )
        
        price_min = display_df["Low"].min()
        price_max = display_df["High"].max()
        price_range = price_max - price_min
        if price_range == 0:
            price_range = price_max * 0.1 or 1.0
        y_min = price_min - price_range * 0.05
        y_max = price_max + price_range * 0.1
        
        fig.update_yaxes(title_text="Price", range=[y_min, y_max], row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=volume_row, col=1)
        
        return fig
    
    def show(self) -> None:
        """Shows the chart in the browser."""
        fig = self.build()
        fig.show()
    
    def save(self, filename: str) -> None:
        """Saves the chart to an HTML file."""
        fig = self.build()
        fig.write_html(filename)
