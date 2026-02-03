"""
Smoke tests that hit the real Xotelo API.
These tests verify the API is accessible and returns expected data structures.

Run with: RUN_API_SMOKE=1 pytest tests/test_api_smoke.py -v -m smoke
Skip with: pytest -m "not smoke"
"""
from datetime import datetime, timedelta
import os

import pytest
import requests

# Mark all tests in this module as smoke tests and guard with env var
pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        os.getenv("RUN_API_SMOKE") != "1",
        reason="Set RUN_API_SMOKE=1 to run API smoke tests"
    ),
]

BASE_URL = "https://data.xotelo.com/api"

# Known valid hotel key for testing (Condado Vanderbilt Hotel)
TEST_HOTEL_KEY = "g147319-d6691692"
# Puerto Rico location key
PR_LOCATION_KEY = "g147319"


class TestXoteloAPIAvailability:
    """Verify the Xotelo API is accessible."""

    def test_api_is_reachable(self):
        """Basic connectivity test."""
        response = requests.get(f"{BASE_URL}/list", params={"location_key": PR_LOCATION_KEY}, timeout=30)
        assert response.status_code == 200

    def test_api_returns_json(self):
        """API returns valid JSON."""
        response = requests.get(f"{BASE_URL}/list", params={"location_key": PR_LOCATION_KEY}, timeout=30)
        data = response.json()
        assert isinstance(data, dict)


class TestListEndpoint:
    """Tests for /list endpoint."""

    def test_list_returns_hotels_for_puerto_rico(self):
        """Verify we can get hotels for Puerto Rico using location_key."""
        response = requests.get(f"{BASE_URL}/list", params={"location_key": PR_LOCATION_KEY}, timeout=30)
        data = response.json()

        assert 'result' in data
        assert data['result'] is not None
        assert 'list' in data['result']
        assert len(data['result']['list']) > 0

    def test_hotel_has_expected_fields(self):
        """Verify hotel objects have key fields."""
        response = requests.get(f"{BASE_URL}/list", params={"location_key": PR_LOCATION_KEY}, timeout=30)
        data = response.json()
        hotel = data['result']['list'][0]

        assert 'key' in hotel
        assert 'name' in hotel


class TestRatesEndpoint:
    """Tests for /rates endpoint."""

    def test_rates_returns_prices(self):
        """Verify we can get rates for a known hotel."""
        checkin = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=31)).strftime("%Y-%m-%d")

        response = requests.get(f"{BASE_URL}/rates", params={
            "hotel_key": TEST_HOTEL_KEY,
            "chk_in": checkin,
            "chk_out": checkout,
            "rooms": 1,
            "adults": 2
        }, timeout=30)

        data = response.json()

        assert response.status_code == 200
        # API should return result (may have rates or not depending on availability)
        assert 'result' in data

    def test_rates_response_structure(self):
        """Verify rates response has expected structure when available."""
        checkin = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=46)).strftime("%Y-%m-%d")

        response = requests.get(f"{BASE_URL}/rates", params={
            "hotel_key": TEST_HOTEL_KEY,
            "chk_in": checkin,
            "chk_out": checkout,
            "rooms": 1,
            "adults": 2
        }, timeout=30)

        data = response.json()

        if data.get('result') and 'rates' in data['result']:
            rates = data['result']['rates']
            if rates:
                # Verify rate object structure
                rate = rates[0]
                assert 'rate' in rate
                assert 'name' in rate

    def test_invalid_hotel_key_handling(self):
        """Invalid hotel key should not crash - returns error or null result."""
        response = requests.get(f"{BASE_URL}/rates", params={
            "hotel_key": "invalid-key-12345",
            "chk_in": "2026-03-01",
            "chk_out": "2026-03-02",
            "rooms": 1,
            "adults": 2
        }, timeout=30)

        data = response.json()

        # API returns 200 but with error or null result for invalid keys
        assert response.status_code == 200
        # Either has error, or result is None/empty
        has_error = 'error' in data
        has_null_result = data.get('result') is None
        has_empty_rates = (data.get('result') or {}).get('rates', []) == []

        assert has_error or has_null_result or has_empty_rates


class TestAPIRateLimits:
    """Tests related to API rate limiting."""

    def test_multiple_requests_succeed(self):
        """Verify we can make multiple requests in succession."""
        import time

        for i in range(3):
            response = requests.get(f"{BASE_URL}/list", params={"location_key": PR_LOCATION_KEY}, timeout=30)
            assert response.status_code == 200
            time.sleep(0.5)  # Respect rate limiting


class TestKnownHotelKey:
    """Tests using known hotel keys from the database."""

    def test_condado_vanderbilt_has_rates(self):
        """Test a specific well-known hotel returns data."""
        checkin = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=61)).strftime("%Y-%m-%d")

        response = requests.get(f"{BASE_URL}/rates", params={
            "hotel_key": TEST_HOTEL_KEY,
            "chk_in": checkin,
            "chk_out": checkout,
            "rooms": 1,
            "adults": 2
        }, timeout=30)

        assert response.status_code == 200
        data = response.json()

        # This is a real hotel, should have valid result structure
        assert 'result' in data
