"""
Price Providers Package - Cascade pipeline for hotel price fetching.

This package provides a multi-source price fetching system that tries
different providers in cascade order to maximize price coverage.

Providers (in priority order):
1. Xotelo - Free, TripAdvisor-based (primary)
2. SerpApi - Google Hotels ($0 for 250/month)
3. Apify - Booking.com scraper ($5/month free tier)
"""
from .base import PriceProvider, PriceResult
from .xotelo import XoteloProvider
from .serpapi import SerpApiProvider
from .apify import ApifyProvider
from .cascade import CascadePriceProvider
from .cache import PriceCache

__all__ = [
    "PriceProvider",
    "PriceResult",
    "XoteloProvider",
    "SerpApiProvider",
    "ApifyProvider",
    "CascadePriceProvider",
    "PriceCache",
]
