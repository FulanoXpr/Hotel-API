"""
Unit tests for xotelo_api.py - the shared API client module.
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xotelo_api import XoteloAPI, RateInfo, HotelInfo, get_client


class TestXoteloAPIInit:
    """Tests for XoteloAPI initialization."""

    def test_default_initialization(self):
        api = XoteloAPI()

        assert api.base_url == "https://data.xotelo.com/api"
        assert api.timeout == 30
        assert api.delay == 0.5
        assert api.max_retries == 2

    def test_custom_initialization(self):
        api = XoteloAPI(
            base_url="https://custom.api.com",
            timeout=60,
            delay=1.0,
            max_retries=5
        )

        assert api.base_url == "https://custom.api.com"
        assert api.timeout == 60
        assert api.delay == 1.0
        assert api.max_retries == 5


class TestXoteloAPIGetRates:
    """Tests for XoteloAPI.get_rates method."""

    @patch.object(XoteloAPI, '_request')
    def test_returns_lowest_rate(self, mock_request):
        mock_request.return_value = {
            'result': {
                'rates': [
                    {'rate': 150, 'name': 'Booking.com', 'code': 'BK'},
                    {'rate': 120, 'name': 'Agoda', 'code': 'AG'},
                    {'rate': 180, 'name': 'Hotels.com', 'code': 'HT'}
                ]
            }
        }

        api = XoteloAPI()
        result = api.get_rates("test-key", "2026-03-01", "2026-03-02")

        assert result is not None
        assert result['rate'] == 120
        assert result['provider'] == 'Agoda'
        assert result['code'] == 'AG'

    @patch.object(XoteloAPI, '_request')
    def test_returns_none_on_empty_rates(self, mock_request):
        mock_request.return_value = {'result': {'rates': []}}

        api = XoteloAPI()
        result = api.get_rates("test-key", "2026-03-01", "2026-03-02")

        assert result is None

    @patch.object(XoteloAPI, '_request')
    def test_returns_none_on_api_failure(self, mock_request):
        mock_request.return_value = None

        api = XoteloAPI()
        result = api.get_rates("test-key", "2026-03-01", "2026-03-02")

        assert result is None

    @patch.object(XoteloAPI, '_request')
    def test_passes_correct_params(self, mock_request):
        mock_request.return_value = {
            'result': {'rates': [{'rate': 100, 'name': 'Test', 'code': 'T'}]}
        }

        api = XoteloAPI()
        api.get_rates("my-key", "2026-03-01", "2026-03-02", rooms=2, adults=3)

        call_params = mock_request.call_args[0][1]
        assert call_params['hotel_key'] == 'my-key'
        assert call_params['chk_in'] == '2026-03-01'
        assert call_params['chk_out'] == '2026-03-02'
        assert call_params['rooms'] == 2
        assert call_params['adults'] == 3


class TestXoteloAPISearchHotel:
    """Tests for XoteloAPI.search_hotel method."""

    @patch.object(XoteloAPI, '_request')
    def test_returns_first_hotel_found(self, mock_request):
        mock_request.return_value = {
            'result': {
                'list': [
                    {'hotel_key': 'key1', 'name': 'Hotel One', 'short_place_name': 'San Juan'},
                    {'hotel_key': 'key2', 'name': 'Hotel Two', 'short_place_name': 'Ponce'}
                ]
            }
        }

        api = XoteloAPI()
        result = api.search_hotel("Hotel")

        assert result is not None
        assert result['key'] == 'key1'
        assert result['name'] == 'Hotel One'
        assert result['location'] == 'San Juan'

    @patch.object(XoteloAPI, '_request')
    def test_returns_none_on_no_results(self, mock_request):
        mock_request.return_value = {'result': {'list': []}}

        api = XoteloAPI()
        result = api.search_hotel("NonexistentHotel")

        assert result is None

    @patch.object(XoteloAPI, '_request')
    def test_returns_none_on_api_failure(self, mock_request):
        mock_request.return_value = None

        api = XoteloAPI()
        result = api.search_hotel("Hotel")

        assert result is None


class TestXoteloAPIListHotels:
    """Tests for XoteloAPI.list_hotels method."""

    @patch.object(XoteloAPI, '_request')
    def test_returns_hotels_and_count(self, mock_request):
        mock_request.return_value = {
            'result': {
                'list': [
                    {'name': 'Hotel A', 'key': 'key-a'},
                    {'name': 'Hotel B', 'key': 'key-b'}
                ],
                'total_count': 100
            }
        }

        api = XoteloAPI()
        hotels, total = api.list_hotels()

        assert len(hotels) == 2
        assert total == 100
        assert hotels[0]['name'] == 'Hotel A'

    @patch.object(XoteloAPI, '_request')
    def test_returns_empty_on_api_failure(self, mock_request):
        mock_request.return_value = None

        api = XoteloAPI()
        hotels, total = api.list_hotels()

        assert hotels == []
        assert total == 0

    @patch.object(XoteloAPI, '_request')
    def test_passes_pagination_params(self, mock_request):
        mock_request.return_value = {'result': {'list': [], 'total_count': 0}}

        api = XoteloAPI()
        api.list_hotels(location_key="custom-key", limit=50, offset=100)

        call_params = mock_request.call_args[0][1]
        assert call_params['location_key'] == 'custom-key'
        assert call_params['limit'] == 50
        assert call_params['offset'] == 100


class TestXoteloAPIRequest:
    """Tests for XoteloAPI._request method (internal)."""

    @patch('xotelo_api.requests.Session.get')
    def test_returns_data_on_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'result': {'data': 'test'}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        api = XoteloAPI()
        result = api._request('/test', {'param': 'value'})

        assert result == {'result': {'data': 'test'}}

    @patch('xotelo_api.requests.Session.get')
    def test_returns_none_on_error_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': 'Something went wrong'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        api = XoteloAPI()
        result = api._request('/test', {})

        assert result is None

    @patch('xotelo_api.requests.Session.get')
    @patch('xotelo_api.time.sleep')
    def test_retries_on_timeout(self, mock_sleep, mock_get):
        import requests
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            MagicMock(
                json=MagicMock(return_value={'result': 'success'}),
                raise_for_status=MagicMock()
            )
        ]

        api = XoteloAPI(max_retries=2)
        result = api._request('/test', {})

        assert result == {'result': 'success'}
        assert mock_get.call_count == 2

    @patch('xotelo_api.requests.Session.get')
    @patch('xotelo_api.time.sleep')
    def test_returns_none_after_max_retries(self, mock_sleep, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        api = XoteloAPI(max_retries=3)
        result = api._request('/test', {})

        assert result is None
        assert mock_get.call_count == 3


class TestXoteloAPIWait:
    """Tests for XoteloAPI.wait method."""

    @patch('xotelo_api.time.sleep')
    def test_sleeps_for_configured_delay(self, mock_sleep):
        api = XoteloAPI(delay=1.5)
        api.wait()

        mock_sleep.assert_called_once_with(1.5)


class TestGetClient:
    """Tests for get_client convenience function."""

    def test_returns_xotelo_api_instance(self):
        # Reset the cached client
        import xotelo_api
        xotelo_api._default_client = None

        client = get_client()

        assert isinstance(client, XoteloAPI)

    def test_returns_same_instance_on_subsequent_calls(self):
        import xotelo_api
        xotelo_api._default_client = None

        client1 = get_client()
        client2 = get_client()

        assert client1 is client2
