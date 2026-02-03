"""
Centralized configuration for Hotel Price Updater.
Uses environment variables with sensible defaults.
"""
import os
from typing import Final

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

# =============================================================================
# CASCADE PIPELINE CONFIGURATION
# =============================================================================

# SerpApi Configuration (Google Hotels)
# Get your API key at: https://serpapi.com/users/sign_up
# Free tier: 250 searches/month
SERPAPI_KEY: Final[str] = os.getenv("SERPAPI_KEY", "")

# Apify Configuration (Booking.com scraper)
# Get your token at: https://console.apify.com/sign-up
# Free tier: $5/month in credits (~1,700 results)
APIFY_TOKEN: Final[str] = os.getenv("APIFY_TOKEN", "")

# Cascade Pipeline Settings
CASCADE_ENABLED: Final[bool] = os.getenv("CASCADE_ENABLED", "true").lower() == "true"
CACHE_TTL_HOURS: Final[int] = int(os.getenv("CACHE_TTL_HOURS", "24"))
CACHE_FILE: Final[str] = os.getenv("CACHE_FILE", "cache/prices_cache.json")
