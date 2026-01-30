"""
Unit tests for xotelo_price_updater.py
"""
import pytest
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xotelo_price_updater as updater
from xotelo_api import XoteloAPI, RateInfo


class TestGetAutoParams:
    """Tests for get_auto_params function."""

    def test_returns_dict_with_required_keys(self):
        params = updater.get_auto_params()

        assert 'chk_in' in params
        assert 'chk_out' in params
        assert 'rooms' in params
        assert 'adults' in params
        assert 'nights' in params

    def test_checkin_is_30_days_ahead(self):
        params = updater.get_auto_params()
        expected_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        assert params['chk_in'] == expected_date

    def test_checkout_is_one_night_after_checkin(self):
        params = updater.get_auto_params()
        checkin = datetime.strptime(params['chk_in'], "%Y-%m-%d")
        checkout = datetime.strptime(params['chk_out'], "%Y-%m-%d")

        assert (checkout - checkin).days == 1

    def test_default_rooms_and_adults(self):
        params = updater.get_auto_params()

        assert params['rooms'] == 1
        assert params['adults'] == 2


class TestLoadHotelKeys:
    """Tests for load_hotel_keys function."""

    def test_loads_keys_from_file(self, tmp_path):
        # Create a test JSON file
        test_keys = {"Hotel A": "key-a", "Hotel B": "key-b"}
        test_file = tmp_path / "test_keys.json"
        test_file.write_text(json.dumps(test_keys))

        with patch.object(updater, 'HOTEL_KEYS_DB', str(test_file)):
            keys = updater.load_hotel_keys()

        assert keys == test_keys

    def test_returns_empty_dict_if_file_not_found(self, tmp_path):
        with patch.object(updater, 'HOTEL_KEYS_DB', str(tmp_path / "nonexistent.json")):
            keys = updater.load_hotel_keys()

        assert keys == {}

    def test_returns_empty_dict_on_invalid_json(self, tmp_path):
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json {{{")

        with patch.object(updater, 'HOTEL_KEYS_DB', str(test_file)):
            keys = updater.load_hotel_keys()

        assert keys == {}


class TestGetHotelRates:
    """Tests for get_hotel_rates wrapper function."""

    @patch.object(XoteloAPI, 'get_rates')
    def test_returns_lowest_rate(self, mock_get_rates):
        mock_get_rates.return_value = RateInfo(
            rate=120,
            provider='Agoda',
            code='AG'
        )

        result = updater.get_hotel_rates("test-key", "2026-03-01", "2026-03-02")

        assert result['rate'] == 120
        assert result['provider'] == 'Agoda'

    @patch.object(XoteloAPI, 'get_rates')
    def test_returns_none_on_empty_rates(self, mock_get_rates):
        mock_get_rates.return_value = None

        result = updater.get_hotel_rates("test-key", "2026-03-01", "2026-03-02")

        assert result is None

    @patch.object(XoteloAPI, 'get_rates')
    def test_returns_none_on_error_response(self, mock_get_rates):
        mock_get_rates.return_value = None

        result = updater.get_hotel_rates("invalid-key", "2026-03-01", "2026-03-02")

        assert result is None

    @patch.object(XoteloAPI, 'get_rates')
    def test_passes_correct_params(self, mock_get_rates):
        mock_get_rates.return_value = RateInfo(rate=100, provider='Test', code='T')

        updater.get_hotel_rates("my-key", "2026-03-01", "2026-03-02", rooms=2, adults=3)

        mock_get_rates.assert_called_once_with(
            "my-key", "2026-03-01", "2026-03-02", 2, 3
        )


class TestConstants:
    """Tests for module constants."""

    def test_base_url_is_xotelo(self):
        assert updater.BASE_URL == "https://data.xotelo.com/api"

    def test_default_days_ahead_is_30(self):
        assert updater.DEFAULT_DAYS_AHEAD == 30

    def test_request_delay_is_reasonable(self):
        assert 0.1 <= updater.REQUEST_DELAY <= 2.0
