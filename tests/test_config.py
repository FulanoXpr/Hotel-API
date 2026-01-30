"""
Unit tests for config.py
"""
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class TestConfigDefaults:
    """Tests for default configuration values."""

    def test_base_url_is_xotelo(self):
        assert config.BASE_URL == "https://data.xotelo.com/api"

    def test_timeout_is_positive(self):
        assert config.TIMEOUT > 0
        assert config.TIMEOUT == 30

    def test_request_delay_is_reasonable(self):
        assert 0.1 <= config.REQUEST_DELAY <= 5.0

    def test_location_key_is_puerto_rico(self):
        assert config.LOCATION_KEY == "g147319"

    def test_default_days_ahead(self):
        assert config.DEFAULT_DAYS_AHEAD == 30

    def test_default_nights(self):
        assert config.DEFAULT_NIGHTS == 1

    def test_default_rooms(self):
        assert config.DEFAULT_ROOMS == 1

    def test_default_adults(self):
        assert config.DEFAULT_ADULTS == 2

    def test_max_retries_is_positive(self):
        assert config.MAX_RETRIES > 0


class TestConfigTypes:
    """Tests for configuration value types."""

    def test_base_url_is_string(self):
        assert isinstance(config.BASE_URL, str)

    def test_timeout_is_int(self):
        assert isinstance(config.TIMEOUT, int)

    def test_request_delay_is_float(self):
        assert isinstance(config.REQUEST_DELAY, float)

    def test_file_paths_are_strings(self):
        assert isinstance(config.EXCEL_FILE, str)
        assert isinstance(config.HOTEL_KEYS_DB, str)
        assert isinstance(config.MAPPING_FILE, str)
        assert isinstance(config.API_HOTELS_CACHE, str)


class TestConfigFileExtensions:
    """Tests for file path extensions."""

    def test_excel_file_has_xlsx_extension(self):
        assert config.EXCEL_FILE.endswith('.xlsx')

    def test_hotel_keys_db_has_json_extension(self):
        assert config.HOTEL_KEYS_DB.endswith('.json')

    def test_mapping_file_has_json_extension(self):
        assert config.MAPPING_FILE.endswith('.json')

    def test_cache_file_has_json_extension(self):
        assert config.API_HOTELS_CACHE.endswith('.json')
