"""
Tests for the CascadePriceProvider.

Tests the cascade orchestration logic, provider ordering, and statistics.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from price_providers.base import PriceProvider, PriceResult
from price_providers.cascade import CascadePriceProvider
from price_providers.cache import PriceCache


class MockProvider(PriceProvider):
    """Mock provider for testing."""

    def __init__(self, name: str, result=None, available: bool = True):
        self._name = name
        self._result = result
        self._available = available
        self.call_count = 0

    def get_price(self, hotel_name, hotel_key, check_in, check_out, rooms=1, adults=2):
        self.call_count += 1
        return self._result

    def get_name(self):
        return self._name

    def is_available(self):
        return self._available


class TestCascadePriceProvider:
    """Tests for CascadePriceProvider."""

    def test_init(self):
        """Test initialization."""
        providers = [MockProvider("mock1"), MockProvider("mock2")]
        cascade = CascadePriceProvider(providers)

        assert len(cascade.providers) == 2
        assert cascade.cache is not None

    def test_get_price_first_provider_succeeds(self):
        """Test that cascade stops when first provider returns a price."""
        result1: PriceResult = {
            "price": 100.0,
            "provider": "Provider1",
            "source": "mock1",
            "cached": False
        }

        provider1 = MockProvider("mock1", result=result1)
        provider2 = MockProvider("mock2", result=None)

        # Use a mock cache to avoid file I/O
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set = Mock()

        cascade = CascadePriceProvider([provider1, provider2], cache=mock_cache)

        result = cascade.get_price(
            "Test Hotel", "key123",
            "2026-03-01", "2026-03-02"
        )

        assert result is not None
        assert result["price"] == 100.0
        assert provider1.call_count == 1
        assert provider2.call_count == 0  # Never called

    def test_get_price_cascade_to_second_provider(self):
        """Test that cascade tries second provider when first returns None."""
        result2: PriceResult = {
            "price": 150.0,
            "provider": "Provider2",
            "source": "mock2",
            "cached": False
        }

        provider1 = MockProvider("mock1", result=None)
        provider2 = MockProvider("mock2", result=result2)

        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set = Mock()

        cascade = CascadePriceProvider([provider1, provider2], cache=mock_cache)

        result = cascade.get_price(
            "Test Hotel", "key123",
            "2026-03-01", "2026-03-02"
        )

        assert result is not None
        assert result["price"] == 150.0
        assert result["source"] == "mock2"
        assert provider1.call_count == 1
        assert provider2.call_count == 1

    def test_get_price_all_providers_fail(self):
        """Test when all providers return None."""
        provider1 = MockProvider("mock1", result=None)
        provider2 = MockProvider("mock2", result=None)

        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set = Mock()

        cascade = CascadePriceProvider([provider1, provider2], cache=mock_cache)

        result = cascade.get_price(
            "Test Hotel", "key123",
            "2026-03-01", "2026-03-02"
        )

        assert result is None
        assert provider1.call_count == 1
        assert provider2.call_count == 1

    def test_get_price_from_cache(self):
        """Test that cached results are returned without calling providers."""
        cached_result: PriceResult = {
            "price": 200.0,
            "provider": "Cached",
            "source": "cache",
            "cached": True
        }

        provider1 = MockProvider("mock1", result=None)

        mock_cache = Mock()
        mock_cache.get.return_value = cached_result

        cascade = CascadePriceProvider([provider1], cache=mock_cache)

        result = cascade.get_price(
            "Test Hotel", "key123",
            "2026-03-01", "2026-03-02"
        )

        assert result is not None
        assert result["cached"] is True
        assert provider1.call_count == 0  # Provider never called

    def test_skips_unavailable_providers(self):
        """Test that unavailable providers are skipped."""
        result2: PriceResult = {
            "price": 175.0,
            "provider": "Provider2",
            "source": "mock2",
            "cached": False
        }

        provider1 = MockProvider("mock1", result=None, available=False)
        provider2 = MockProvider("mock2", result=result2, available=True)

        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set = Mock()

        cascade = CascadePriceProvider([provider1, provider2], cache=mock_cache)

        result = cascade.get_price(
            "Test Hotel", "key123",
            "2026-03-01", "2026-03-02"
        )

        assert result is not None
        assert result["price"] == 175.0
        assert provider1.call_count == 0  # Skipped
        assert provider2.call_count == 1

    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        result1: PriceResult = {
            "price": 100.0,
            "provider": "Test",
            "source": "mock1",
            "cached": False
        }

        provider1 = MockProvider("mock1", result=result1)
        provider2 = MockProvider("mock2", result=None)

        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set = Mock()

        cascade = CascadePriceProvider([provider1, provider2], cache=mock_cache)

        # Make multiple calls
        cascade.get_price("Hotel A", "key1", "2026-03-01", "2026-03-02")
        cascade.get_price("Hotel B", "key2", "2026-03-01", "2026-03-02")

        stats = cascade.get_stats()
        assert stats["total"] == 2
        assert stats["mock1"] == 2
        assert stats["not_found"] == 0

    def test_statistics_with_cache_hits(self):
        """Test statistics with cache hits."""
        cached_result: PriceResult = {
            "price": 200.0,
            "provider": "Cached",
            "source": "cache",
            "cached": True
        }

        provider1 = MockProvider("mock1", result=None)

        mock_cache = Mock()
        mock_cache.get.return_value = cached_result

        cascade = CascadePriceProvider([provider1], cache=mock_cache)

        cascade.get_price("Hotel A", "key1", "2026-03-01", "2026-03-02")

        stats = cascade.get_stats()
        assert stats["total"] == 1
        assert stats["cache"] == 1

    def test_get_stats_summary(self):
        """Test formatted statistics summary."""
        result1: PriceResult = {
            "price": 100.0,
            "provider": "Test",
            "source": "mock1",
            "cached": False
        }

        provider1 = MockProvider("mock1", result=result1)
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set = Mock()

        cascade = CascadePriceProvider([provider1], cache=mock_cache)
        cascade.get_price("Hotel A", "key1", "2026-03-01", "2026-03-02")

        summary = cascade.get_stats_summary()

        assert "Hotels processed: 1" in summary
        assert "TOTAL COVERAGE:" in summary
        assert "100.0%" in summary

    def test_reset_stats(self):
        """Test resetting statistics."""
        provider1 = MockProvider("mock1", result=None)
        mock_cache = Mock()
        mock_cache.get.return_value = None

        cascade = CascadePriceProvider([provider1], cache=mock_cache)

        cascade.get_price("Hotel A", "key1", "2026-03-01", "2026-03-02")
        assert cascade.stats["total"] == 1

        cascade.reset_stats()
        assert cascade.stats["total"] == 0

    def test_get_available_providers(self):
        """Test listing available providers."""
        provider1 = MockProvider("mock1", available=True)
        provider2 = MockProvider("mock2", available=False)
        provider3 = MockProvider("mock3", available=True)

        mock_cache = Mock()
        cascade = CascadePriceProvider([provider1, provider2, provider3], cache=mock_cache)

        available = cascade.get_available_providers()
        assert available == ["mock1", "mock3"]
