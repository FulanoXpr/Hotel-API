"""
Unit tests for xotelo_price_fixer.py
"""
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xotelo_price_fixer as fixer
from xotelo_api import XoteloAPI, HotelInfo, RateInfo


class TestSearchHotel:
    """Tests for search_hotel function."""

    def test_returns_hotel_info_on_success(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.search_hotel.return_value = HotelInfo(
            key='test-key',
            name='Test Hotel',
            location='San Juan'
        )

        result = fixer.search_hotel(mock_api, "Test Hotel")

        assert result is not None
        assert result['key'] == 'test-key'
        assert result['name'] == 'Test Hotel'

    def test_returns_none_on_not_found(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.search_hotel.return_value = None

        result = fixer.search_hotel(mock_api, "NonexistentHotel")

        assert result is None


class TestGetHotelRates:
    """Tests for get_hotel_rates function."""

    def test_returns_rate_info_on_success(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.get_rates.return_value = RateInfo(
            rate=150.0,
            provider='Booking.com',
            code='BK'
        )

        result = fixer.get_hotel_rates(mock_api, "test-key", "2026-03-01", "2026-03-02")

        assert result is not None
        assert result['rate'] == 150.0
        assert result['provider'] == 'Booking.com'

    def test_returns_none_on_no_rates(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.get_rates.return_value = None

        result = fixer.get_hotel_rates(mock_api, "test-key", "2026-03-01", "2026-03-02")

        assert result is None

    def test_uses_provided_dates(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.get_rates.return_value = None

        fixer.get_hotel_rates(mock_api, "test-key", "2026-03-01", "2026-03-02")

        mock_api.get_rates.assert_called_once_with(
            "test-key",
            "2026-03-01",
            "2026-03-02"
        )


class TestProcessUnmatchedHotels:
    """Tests for process_unmatched_hotels function."""

    def test_searches_hotel_and_updates_worksheet(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.search_hotel.return_value = HotelInfo(
            key='found-key',
            name='Found Hotel',
            location='Puerto Rico'
        )
        mock_api.get_rates.return_value = RateInfo(
            rate=100.0,
            provider='Agoda',
            code='AG'
        )
        mock_api.wait.return_value = None

        mock_ws = MagicMock()

        no_match = [(2, "Test Hotel")]

        updated = fixer.process_unmatched_hotels(
            mock_api, mock_ws, no_match,
            price_col=3, provider_col=4, match_col=5, score_col=6, key_col=7,
            check_in_date="2026-03-01", check_out_date="2026-03-02"
        )

        assert updated == 1
        mock_ws.cell.assert_any_call(row=2, column=3, value=100.0)
        mock_ws.cell.assert_any_call(row=2, column=4, value='Agoda')
        mock_ws.cell.assert_any_call(row=2, column=7, value='found-key')

    def test_skips_hotels_not_in_puerto_rico(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.search_hotel.return_value = HotelInfo(
            key='wrong-key',
            name='Wrong Hotel',
            location='Florida'  # Not Puerto Rico
        )
        mock_api.wait.return_value = None

        mock_ws = MagicMock()

        no_match = [(2, "Test Hotel")]

        updated = fixer.process_unmatched_hotels(
            mock_api, mock_ws, no_match,
            price_col=3, provider_col=4, match_col=5, score_col=6, key_col=7,
            check_in_date="2026-03-01", check_out_date="2026-03-02"
        )

        assert updated == 0
        # Should mark as "Not found"
        mock_ws.cell.assert_any_call(row=2, column=4, value="Not found")

    def test_tries_multiple_search_variations(self):
        mock_api = MagicMock(spec=XoteloAPI)
        # First 3 searches return None, 4th returns result
        mock_api.search_hotel.side_effect = [
            None, None, None,
            HotelInfo(key='found-key', name='Found', location='Puerto Rico')
        ]
        mock_api.get_rates.return_value = None
        mock_api.wait.return_value = None

        mock_ws = MagicMock()

        # Hotel name with parentheses will trigger multiple variations
        no_match = [(2, "Test Hotel (Downtown)")]

        fixer.process_unmatched_hotels(
            mock_api, mock_ws, no_match,
            price_col=3, provider_col=4, match_col=5, score_col=6, key_col=7,
            check_in_date="2026-03-01", check_out_date="2026-03-02"
        )

        # Should have tried multiple search variations
        assert mock_api.search_hotel.call_count >= 2


class TestProcessNoPriceHotels:
    """Tests for process_no_price_hotels function."""

    def test_retries_getting_price(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.get_rates.return_value = RateInfo(
            rate=200.0,
            provider='Hotels.com',
            code='HC'
        )
        mock_api.wait.return_value = None

        mock_ws = MagicMock()

        no_price = [(2, "Test Hotel", "Matched Name", "existing-key")]

        updated = fixer.process_no_price_hotels(
            mock_api, mock_ws, no_price,
            price_col=3, provider_col=4,
            check_in_date="2026-03-01", check_out_date="2026-03-02"
        )

        assert updated == 1
        mock_ws.cell.assert_any_call(row=2, column=3, value=200.0)
        mock_ws.cell.assert_any_call(row=2, column=4, value='Hotels.com')

    def test_handles_still_no_price(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.get_rates.return_value = None
        mock_api.wait.return_value = None

        mock_ws = MagicMock()

        no_price = [(2, "Test Hotel", "Matched Name", "existing-key")]

        updated = fixer.process_no_price_hotels(
            mock_api, mock_ws, no_price,
            price_col=3, provider_col=4,
            check_in_date="2026-03-01", check_out_date="2026-03-02"
        )

        assert updated == 0
        mock_ws.cell.assert_any_call(row=2, column=4, value="No price available")

    def test_handles_missing_hotel_key(self):
        mock_api = MagicMock(spec=XoteloAPI)
        mock_api.wait.return_value = None

        mock_ws = MagicMock()

        no_price = [(2, "Test Hotel", "Matched Name", None)]

        updated = fixer.process_no_price_hotels(
            mock_api, mock_ws, no_price,
            price_col=3, provider_col=4,
            check_in_date="2026-03-01", check_out_date="2026-03-02"
        )

        assert updated == 0
        # Should not call get_rates when hotel_key is None
        mock_api.get_rates.assert_not_called()


class TestResolveDates:
    """Tests for date resolution helper."""

    def test_resolve_dates_with_explicit_dates(self):
        args = type("Args", (), {
            "check_in": "2026-03-01",
            "check_out": "2026-03-02",
            "days_ahead": 30,
            "nights": 1
        })()

        check_in, check_out = fixer.resolve_dates(args)

        assert check_in == "2026-03-01"
        assert check_out == "2026-03-02"

    def test_resolve_dates_with_relative_defaults(self):
        args = type("Args", (), {
            "check_in": None,
            "check_out": None,
            "days_ahead": 30,
            "nights": 2
        })()

        check_in, check_out = fixer.resolve_dates(args)

        expected_check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        expected_check_out = (datetime.strptime(expected_check_in, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")

        assert check_in == expected_check_in
        assert check_out == expected_check_out
