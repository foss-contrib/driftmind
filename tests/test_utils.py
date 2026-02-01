"""Tests for driftmind.utils module."""

import os
from unittest.mock import patch

import pandas as pd
import pytest

from driftmind.exceptions import DriftMindConfigError
from driftmind.utils.helpers import (
    convert_java_to_strftime,
    convert_strftime_to_java,
    load_credentials,
    plot_actual_vs_predicted,
    plot_time_series,
    smart_parse_date,
)


class TestLoadCredentials:
    """Test credential loading from environment."""

    def test_load_from_env_success(self):
        """Test loading credentials from environment variables."""
        with patch.dict(
            os.environ,
            {"DRIFTMIND_API_KEY": "test-key", "DRIFTMIND_API_URL": "https://test.com"},
        ):
            creds = load_credentials(use_dotenv=False)
            assert creds["DRIFTMIND_API_KEY"] == "test-key"
            assert creds["DRIFTMIND_API_URL"] == "https://test.com"

    def test_missing_api_key_error(self):
        """Test error when API key is missing."""
        with patch.dict(
            os.environ, {"DRIFTMIND_API_URL": "https://test.com"}, clear=True
        ):
            with pytest.raises(DriftMindConfigError, match="Missing DRIFTMIND_API_KEY"):
                load_credentials(use_dotenv=False)

    def test_missing_api_url_error(self):
        """Test error when API URL is missing."""
        with patch.dict(os.environ, {"DRIFTMIND_API_KEY": "test-key"}, clear=True):
            with pytest.raises(DriftMindConfigError, match="Missing DRIFTMIND_API_KEY"):
                load_credentials(use_dotenv=False)

    def test_dotenv_not_installed_error(self):
        """Test error when dotenv requested but not installed."""
        with patch("driftmind.utils.helpers.load_dotenv", None):
            with pytest.raises(
                DriftMindConfigError, match="python-dotenv is not installed"
            ):
                load_credentials(use_dotenv=True)

    def test_load_with_dotenv_path(self, tmp_path):
        """Test loading from explicit .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "DRIFTMIND_API_KEY=dotenv-key\nDRIFTMIND_API_URL=https://dotenv.com\n"
        )

        creds = load_credentials(use_dotenv=True, dotenv_path=env_file)
        assert creds["DRIFTMIND_API_KEY"] == "dotenv-key"
        assert creds["DRIFTMIND_API_URL"] == "https://dotenv.com"


class TestPlotting:
    """Test plotting functions."""

    @patch("driftmind.utils.helpers.plt.show")
    @patch("driftmind.utils.helpers.plt")
    def test_plot_actual_vs_predicted(self, mock_plt, mock_show):
        """Test plotting actual vs predicted values."""
        df = pd.DataFrame(
            {
                "timestamp": [1, 2, 3],
                "expected": [10, 20, 30],
                "predicted": [12, 19, 31],
            }
        )

        plot_actual_vs_predicted(df, "test_var")

        mock_plt.figure.assert_called_once_with(figsize=(15, 4))
        mock_plt.show.assert_called_once()

    @patch("driftmind.utils.helpers.plt.show")
    def test_plot_actual_vs_predicted_empty(self, mock_show):
        """Test plotting with empty dataframe."""
        df = pd.DataFrame()
        plot_actual_vs_predicted(df, "test_var")
        mock_show.assert_not_called()

    def test_plot_actual_vs_predicted_missing_column(self):
        """Test error when required column is missing."""
        df = pd.DataFrame({"timestamp": [1, 2]})
        with pytest.raises(KeyError, match="expected"):
            plot_actual_vs_predicted(df, "test_var")

    @patch("driftmind.utils.helpers.plt.show")
    @patch("driftmind.utils.helpers.plt")
    def test_plot_time_series(self, mock_plt, mock_show):
        """Test plotting time series."""
        plot_time_series([1, 2, 3], [10, 20, 30], "Title", "X", "Y")
        mock_plt.figure.assert_called_once_with(figsize=(15, 3))
        mock_plt.show.assert_called_once()

    @patch("driftmind.utils.helpers.plt.show")
    def test_plot_time_series_empty(self, mock_show):
        """Test plotting empty time series."""
        plot_time_series([], [], "Title", "X", "Y")
        mock_show.assert_not_called()


class TestDateConversion:
    """Test date parsing and format conversion."""

    def test_smart_parse_date_string(self):
        """Test parsing date string."""
        result = smart_parse_date("31-12-2025")
        assert result.day == 31
        assert result.month == 12
        assert result.year == 2025

    def test_smart_parse_date_non_string(self):
        """Test non-string input returns as-is."""
        assert smart_parse_date(123) == 123
        assert smart_parse_date(None) is None

    def test_smart_parse_date_invalid(self):
        """Test invalid date string returns as-is."""
        assert smart_parse_date("not-a-date") == "not-a-date"

    def test_convert_strftime_to_java(self):
        """Test Python to Java date format conversion."""
        assert convert_strftime_to_java("%d-%m-%Y %H:%M:%S") == "dd-MM-yyyy HH:mm:ss"
        assert convert_strftime_to_java("%Y/%m/%d") == "yyyy/MM/dd"

    def test_convert_java_to_strftime(self):
        """Test Java to Python date format conversion."""
        assert convert_java_to_strftime("dd-MM-yyyy HH:mm:ss") == "%d-%m-%Y %H:%M:%S"
        assert convert_java_to_strftime("yyyy/MM/dd") == "%Y/%m/%d"
