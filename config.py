"""
Centralized configuration for Hotel Price Updater.
Uses environment variables with sensible defaults.
"""
import os
from typing import Final

# Xotelo API Configuration
BASE_URL: Final[str] = os.getenv("XOTELO_API_URL", "https://data.xotelo.com/api")
TIMEOUT: Final[int] = int(os.getenv("API_TIMEOUT", "30"))
REQUEST_DELAY: Final[float] = float(os.getenv("REQUEST_DELAY", "0.5"))

# Location Configuration
LOCATION_KEY: Final[str] = os.getenv("PR_LOCATION_KEY", "g147319")  # Puerto Rico

# File Paths
EXCEL_FILE: Final[str] = os.getenv("EXCEL_FILE", "PRTC Endorsed Hotels (12.25).xlsx")
HOTEL_KEYS_DB: Final[str] = os.getenv("HOTEL_KEYS_DB", "hotel_keys_db.json")
MAPPING_FILE: Final[str] = os.getenv("MAPPING_FILE", "hotel_mapping.json")
API_HOTELS_CACHE: Final[str] = os.getenv("API_HOTELS_CACHE", "api_hotels_cache.json")

# Default Search Parameters
DEFAULT_DAYS_AHEAD: Final[int] = int(os.getenv("DEFAULT_DAYS_AHEAD", "30"))
DEFAULT_NIGHTS: Final[int] = int(os.getenv("DEFAULT_NIGHTS", "1"))
DEFAULT_ROOMS: Final[int] = int(os.getenv("DEFAULT_ROOMS", "1"))
DEFAULT_ADULTS: Final[int] = int(os.getenv("DEFAULT_ADULTS", "2"))

# Request Configuration
MAX_RETRIES: Final[int] = int(os.getenv("MAX_RETRIES", "2"))
RETRY_DELAY: Final[float] = float(os.getenv("RETRY_DELAY", "2.0"))
