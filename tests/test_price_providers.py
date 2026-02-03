"""
Tests for price providers.

Tests the base interface and individual provider implementations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from price_providers.base import PriceProvider, PriceResult
from price_providers.xotelo import XoteloProvider
from price_providers.serpapi import SerpApiProvider
from price_providers.apify import ApifyProvider


class TestPriceResult:
    """Tests for PriceResult TypedDict."""

    def test_price_result_structure(self):
        """Test that PriceResult has the expected structure."""
        result: PriceResult = {
            "price": 150.0,
            "provider": "Booking.com",
            "source": "serpapi",
            "cached": False
        }
        assert result["price"] == 150.0
        assert result["provider"] == "Booking.com"
        assert result["source"] == "serpapi"
        assert result["cached"] is False


class TestXoteloProvider:
    """Tests for XoteloProvider."""

    def test_get_name(self):
        """Test provider name."""
        provider = XoteloProvider()
        assert provider.get_name() == "xotelo"

    def test_is_available(self):
        """Xotelo should always be available."""
        provider = XoteloProvider()
        assert provider.is_available() is True

    def test_get_price_no_key(self):
        """Test that get_price returns None when no hotel key provided."""
        provider = XoteloProvider()
        result = provider.get_price(
            hotel_name="Test Hotel",
            hotel_key=None,
            check_in="2026-03-01",
            check_out="2026-03-02"
        )
        assert result is None

    def test_get_price_with_key(self):
        """Test get_price with a valid key (mocked API)."""
        mock_api = Mock()
        mock_api.get_rates.return_value = {
            "rate": 150.0,
            "provider": "Hotels.com",
            "code": "HC"
        }

        provider = XoteloProvider(api=mock_api)
        result = provider.get_price(
            hotel_name="Test Hotel",
            hotel_key="g147319-d12345",
            check_in="2026-03-01",
            check_out="2026-03-02"
        )

        assert result is not None
        assert result["price"] == 150.0
        assert result["provider"] == "Hotels.com"
        assert result["source"] == "xotelo"
        assert result["cached"] is False

    def test_get_price_api_returns_none(self):
        """Test get_price when API returns None."""
        mock_api = Mock()
        mock_api.get_rates.return_value = None

        provider = XoteloProvider(api=mock_api)
        result = provider.get_price(
            hotel_name="Test Hotel",
            hotel_key="g147319-d12345",
            check_in="2026-03-01",
            check_out="2026-03-02"
        )

        assert result is None

    def test_multi_date_mode(self):
        """Test multi-date mode tries different dates."""
        mock_api = Mock()
        # Return None for first date, price for second
        mock_api.get_rates.side_effect = [None, {"rate": 200.0, "provider": "Expedia", "code": "EX"}]
        mock_api.wait = Mock()

        provider = XoteloProvider(api=mock_api)
        provider.set_multi_date_ranges([
            {"label": "+30d", "chk_in": "2026-03-01", "chk_out": "2026-03-02"},
            {"label": "weekend", "chk_in": "2026-03-07", "chk_out": "2026-03-08"}
        ])

        result = provider.get_price(
            hotel_name="Test Hotel",
            hotel_key="g147319-d12345",
            check_in="2026-03-01",
            check_out="2026-03-02"
        )

        assert result is not None
        assert result["price"] == 200.0
        assert "weekend" in result["source"]
        assert mock_api.get_rates.call_count == 2


class TestSerpApiProvider:
    """Tests for SerpApiProvider."""

    def test_get_name(self):
        """Test provider name."""
        provider = SerpApiProvider()
        assert provider.get_name() == "serpapi"

    def test_is_available_without_key(self):
        """Should not be available without API key."""
        with patch.dict(os.environ, {}, clear=True):
            provider = SerpApiProvider(api_key="")
            assert provider.is_available() is False

    def test_is_available_with_key(self):
        """Should be available with API key."""
        provider = SerpApiProvider(api_key="test_key")
        # Will be False if serpapi library isn't installed
        # but test passes as long as the logic is correct
        expected = True  # Assuming serpapi is installed
        try:
            from serpapi import GoogleSearch
            assert provider.is_available() is True
        except ImportError:
            assert provider.is_available() is False

    @patch('price_providers.serpapi.SERPAPI_AVAILABLE', True)
    def test_find_best_match_exact(self):
        """Test name matching with exact match."""
        provider = SerpApiProvider(api_key="test")
        properties = [
            {"name": "Other Hotel"},
            {"name": "Condado Vanderbilt Hotel"},
            {"name": "Another Place"}
        ]
        result = provider._find_best_match("Condado Vanderbilt Hotel", properties)
        assert result is not None
        assert result["name"] == "Condado Vanderbilt Hotel"

    @patch('price_providers.serpapi.SERPAPI_AVAILABLE', True)
    def test_find_best_match_partial(self):
        """Test name matching with partial match."""
        provider = SerpApiProvider(api_key="test")
        properties = [
            {"name": "Some Other Hotel"},
            {"name": "Vanderbilt Condado Resort & Spa"},
        ]
        result = provider._find_best_match("Condado Vanderbilt", properties)
        assert result is not None
        assert "Vanderbilt" in result["name"]

    @patch('price_providers.serpapi.SERPAPI_AVAILABLE', True)
    def test_extract_price_from_rate(self):
        """Test price extraction from rate_per_night."""
        provider = SerpApiProvider(api_key="test")
        property_data = {
            "name": "Test Hotel",
            "rate_per_night": {"lowest": "$150"}
        }
        price = provider._extract_price(property_data)
        assert price == 150.0

    @patch('price_providers.serpapi.SERPAPI_AVAILABLE', True)
    def test_extract_price_from_total(self):
        """Test price extraction from total_rate."""
        provider = SerpApiProvider(api_key="test")
        property_data = {
            "name": "Test Hotel",
            "total_rate": {"lowest": "200.50"}
        }
        price = provider._extract_price(property_data)
        assert price == 200.50


class TestApifyProvider:
    """Tests for ApifyProvider."""

    def test_get_name(self):
        """Test provider name."""
        provider = ApifyProvider()
        assert provider.get_name() == "apify"

    def test_is_available_without_token(self):
        """Should not be available without API token."""
        with patch.dict(os.environ, {}, clear=True):
            provider = ApifyProvider(api_token="")
            assert provider.is_available() is False

    def test_is_available_with_token(self):
        """Should be available with API token."""
        provider = ApifyProvider(api_token="test_token")
        try:
            from apify_client import ApifyClient
            assert provider.is_available() is True
        except ImportError:
            assert provider.is_available() is False

    @patch('price_providers.apify.APIFY_AVAILABLE', True)
    def test_find_best_match(self):
        """Test name matching logic."""
        provider = ApifyProvider(api_token="test")
        items = [
            {"name": "Random Hotel"},
            {"name": "El San Juan Hotel, Curio Collection"},
            {"name": "Another Place"}
        ]
        result = provider._find_best_match("El San Juan Hotel", items)
        assert result is not None
        assert "San Juan" in result["name"]

    @patch('price_providers.apify.APIFY_AVAILABLE', True)
    def test_extract_price_string(self):
        """Test price extraction from string."""
        provider = ApifyProvider(api_token="test")
        item = {"price": "$175.00"}
        price = provider._extract_price(item)
        assert price == 175.0

    @patch('price_providers.apify.APIFY_AVAILABLE', True)
    def test_extract_price_numeric(self):
        """Test price extraction from numeric value."""
        provider = ApifyProvider(api_token="test")
        item = {"priceNumeric": 225.50}
        price = provider._extract_price(item)
        assert price == 225.50

    @patch('price_providers.apify.APIFY_AVAILABLE', True)
    def test_extract_price_nested(self):
        """Test price extraction from nested structure."""
        provider = ApifyProvider(api_token="test")
        item = {
            "priceBreakdown": {
                "grossPrice": {"value": 300.0}
            }
        }
        price = provider._extract_price(item)
        assert price == 300.0
