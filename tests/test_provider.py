"""Tests for DataProvider (data/provider.py)."""

from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from fin_pocket.data.provider import DataProvider


def _make_history_df(tz=None):
    dates = pd.bdate_range("2024-01-02", periods=10, tz=tz)
    return pd.DataFrame(
        {
            "Open": range(10),
            "High": range(10),
            "Low": range(10),
            "Close": range(10),
            "Volume": range(10),
        },
        index=dates,
    )


class TestDataProvider:
    def test_ticker_uppercased(self):
        dp = DataProvider("aapl")
        assert dp.ticker == "AAPL"

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_with_period(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _make_history_df()
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("AAPL")
        df = dp.fetch(period="1y", interval="1d")

        mock_ticker.history.assert_called_once_with(period="1y", interval="1d")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_with_start_end(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _make_history_df()
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("GOOG")
        df = dp.fetch(start="2024-01-01", end="2024-06-01", interval="1d")

        mock_ticker.history.assert_called_once_with(
            start="2024-01-01", end="2024-06-01", interval="1d"
        )
        assert len(df) == 10

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_connection_error(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("Network error")
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("FAIL")
        with pytest.raises(ConnectionError, match="Failed to fetch data for FAIL"):
            dp.fetch()

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_empty_data(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("EMPTY")
        with pytest.raises(ValueError, match="No data available"):
            dp.fetch()

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_none_data(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = None
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("NULL")
        with pytest.raises(ValueError, match="No data available"):
            dp.fetch()

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_missing_columns(self, mock_yf):
        mock_ticker = MagicMock()
        dates = pd.bdate_range("2024-01-02", periods=5)
        mock_ticker.history.return_value = pd.DataFrame(
            {"Close": range(5), "Volume": range(5)}, index=dates
        )
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("BAD")
        with pytest.raises(ValueError, match="Missing columns"):
            dp.fetch()

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_strips_timezone(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _make_history_df(tz="US/Eastern")
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("TZ")
        df = dp.fetch()
        assert df.index.tz is None

    @patch("fin_pocket.data.provider.yf")
    def test_fetch_no_tz_stays_none(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _make_history_df(tz=None)
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("NOTZ")
        df = dp.fetch()
        assert df.index.tz is None

    @patch("fin_pocket.data.provider.yf")
    def test_data_property_after_fetch(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _make_history_df()
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("PROP")
        dp.fetch()
        assert isinstance(dp.data, pd.DataFrame)
        assert len(dp.data) == 10

    def test_data_property_before_fetch(self):
        dp = DataProvider("NOFETCH")
        with pytest.raises(ValueError, match="Data not loaded"):
            _ = dp.data

    @patch("fin_pocket.data.provider.yf")
    def test_get_info(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Apple Inc."}
        mock_yf.Ticker.return_value = mock_ticker

        dp = DataProvider("AAPL")
        info = dp.get_info()
        assert info == {"shortName": "Apple Inc."}
