import yfinance as yf
import pandas as pd


class DataProvider:
    """Class for fetching historical data from Yahoo Finance."""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self._data: pd.DataFrame | None = None
    
    def fetch(
        self,
        period: str = "2y",
        interval: str = "1d",
        start: str | None = None,
        end: str | None = None
    ) -> pd.DataFrame:
        """
        Fetches data from Yahoo Finance.
        
        Args:
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date (YYYY-MM-DD), overrides period
            end: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        
        Raises:
            ConnectionError: If Yahoo Finance is unreachable
            ValueError: If no data is returned for the ticker
        """
        try:
            ticker_obj = yf.Ticker(self.ticker)
            
            if start:
                self._data = ticker_obj.history(start=start, end=end, interval=interval)
            else:
                self._data = ticker_obj.history(period=period, interval=interval)
        except Exception as exc:
            raise ConnectionError(
                f"Failed to fetch data for {self.ticker}: {exc}"
            ) from exc
        
        if self._data is None or self._data.empty:
            raise ValueError(f"No data available for ticker {self.ticker}")
        
        required = {"Open", "High", "Low", "Close", "Volume"}
        missing = required - set(self._data.columns)
        if missing:
            raise ValueError(f"Missing columns in data: {missing}")
        
        self._data.index = pd.to_datetime(self._data.index)
        if self._data.index.tz is not None:
            self._data.index = self._data.index.tz_localize(None)
        
        return self._data
    
    @property
    def data(self) -> pd.DataFrame:
        """Returns the loaded data."""
        if self._data is None:
            raise ValueError("Data not loaded. Call fetch() first")
        return self._data
    
    def get_info(self) -> dict:
        """Returns company information."""
        return yf.Ticker(self.ticker).info
