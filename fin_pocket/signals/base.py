from abc import ABC, abstractmethod
import pandas as pd
import plotly.graph_objects as go


class BaseSignal(ABC):
    """Base class for all signals."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Signal name."""
        pass  # pragma: no cover
    
    @property
    def panel(self) -> str:
        """
        Panel for display: 'main' or 'separate'.
        If 'separate' — signal will get a separate subplot.
        """
        return "main"
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates indicator/signal based on data.
        
        Args:
            data: DataFrame with OHLCV data
        
        Returns:
            DataFrame with additional columns for indicator
        """
        pass  # pragma: no cover
    
    @abstractmethod
    def plot(self, fig: go.Figure, data: pd.DataFrame, row: int = 1) -> go.Figure:
        """
        Adds signal visualization to the chart.
        
        Args:
            fig: Plotly Figure object
            data: DataFrame with calculated data
            row: Row number for display
        
        Returns:
            Updated Figure object
        """
        pass  # pragma: no cover
