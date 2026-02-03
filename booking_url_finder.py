"""
Booking URL Finder - Searches for hotel URLs on Booking.com

Uses SerpApi (Google) to find Booking.com URLs for hotels.
This is more cost-effective than using Apify for URL discovery.

Usage:
    python booking_url_finder.py                    # Find URLs for all hotels without booking_url
    python booking_url_finder.py --hotel "Hotel Name"  # Find URL for specific hotel
    python booking_url_finder.py --limit 10         # Limit to first N hotels
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests

import config

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

HOTEL_KEYS_DB = config.HOTEL_KEYS_DB


def normalize_name(name: str) -> set:
    """Normalize hotel name to set of keywords for matching."""
    import re
    # Remove special chars, lowercase, split into words
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    words = set(name.split())
    # Remove common words
    stop_words = {'the', 'a', 'an', 'hotel', 'resort', 'and', 'by', 'at', 'de', 'la', 'el'}
    return words - stop_words


def search_booking_url_google(hotel_name: str, api_key: str) -> Optional[str]:
    """
    Search for Booking.com URL using Google via SerpApi.

    Args:
        hotel_name: Hotel name to search for
        api_key: SerpApi API key

    Returns:
        Booking.com URL if found, None otherwise
    """
    try:
        from serpapi import GoogleSearch
    except ImportError:
        logger.error("serpapi not installed. Run: pip install google-search-results")
        return None

    # Search Google for the hotel on Booking.com
    params = {
        "engine": "google",
        "q": f'site:booking.com/hotel/pr "{hotel_name}"',
        "api_key": api_key,
        "num": 10
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        organic_results = results.get("organic_results", [])
        hotel_keywords = normalize_name(hotel_name)

        best_match = None
        best_score = 0

        for result in organic_results:
            link = result.get("link", "")
            title = result.get("title", "")

            # Only consider hotel URLs on booking.com
            if "booking.com/hotel/" not in link:
                continue

            # Check title similarity
            title_keywords = normalize_name(title)
            overlap = len(hotel_keywords & title_keywords)

            # Require at least 2 matching keywords
            if overlap >= 2 and overlap > best_score:
                best_score = overlap
                # Clean the URL
                base_url = link.split("?")[0]
                if not base_url.endswith(".html"):
                    base_url += ".html"
                best_match = base_url

        return best_match

    except Exception as e:
        logger.error("Error searching for %s: %s", hotel_name, e)
        return None


def search_booking_url_direct(hotel_name: str) -> Optional[str]:
    """
    Try to construct Booking.com URL from hotel name.

    This is a heuristic approach that works for many hotels.

    Args:
        hotel_name: Hotel name

    Returns:
        Potential Booking.com URL if valid, None otherwise
    """
    import re

    # Normalize the hotel name for URL
    name = hotel_name.lower()

    # Remove common suffixes
    name = re.sub(r'\s*\(.*?\)\s*', '', name)  # Remove parentheses content
    name = re.sub(r'\s*-\s*', ' ', name)  # Replace dashes with spaces

    # Convert to URL-friendly format
    name = re.sub(r'[^a-z0-9\s]', '', name)  # Remove special chars
    name = re.sub(r'\s+', '-', name.strip())  # Spaces to dashes

    # Construct potential URL
    url = f"https://www.booking.com/hotel/pr/{name}.html"

    # Verify the URL exists
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code == 200:
            return response.url.split("?")[0]  # Return final URL without params
    except requests.RequestException:
        pass

    return None


def load_hotel_keys() -> dict:
    """Load hotel keys database."""
    if not os.path.exists(HOTEL_KEYS_DB):
        logger.error("Hotel keys database not found: %s", HOTEL_KEYS_DB)
        return {}

    try:
        with open(HOTEL_KEYS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load hotel keys: %s", e)
        return {}


def save_hotel_keys(hotel_keys: dict) -> None:
    """Save hotel keys database."""
    try:
        with open(HOTEL_KEYS_DB, 'w', encoding='utf-8') as f:
            json.dump(hotel_keys, f, indent=2, ensure_ascii=False)
        logger.info("Saved to %s", HOTEL_KEYS_DB)
    except OSError as e:
        logger.error("Failed to save hotel keys: %s", e)


def migrate_to_new_format(hotel_keys: dict) -> dict:
    """
    Migrate from old format (string) to new format (dict).

    Old: {"Hotel Name": "xotelo_key"}
    New: {"Hotel Name": {"xotelo": "xotelo_key", "booking_url": "..."}}
    """
    migrated = {}
    for name, value in hotel_keys.items():
        if isinstance(value, str):
            migrated[name] = {"xotelo": value}
        else:
            migrated[name] = value
    return migrated


def find_booking_urls(
    hotel_keys: dict,
    api_key: str,
    limit: int = 0,
    specific_hotel: Optional[str] = None
) -> dict:
    """
    Find Booking.com URLs for hotels.

    Args:
        hotel_keys: Hotel keys database
        api_key: SerpApi API key
        limit: Maximum hotels to process (0 = all)
        specific_hotel: Only process this hotel

    Returns:
        Updated hotel keys dict
    """
    # Migrate to new format if needed
    hotel_keys = migrate_to_new_format(hotel_keys)

    # Filter hotels to process
    if specific_hotel:
        hotels_to_process = [(specific_hotel, hotel_keys.get(specific_hotel, {}))]
    else:
        # Only process hotels without booking_url
        hotels_to_process = [
            (name, data) for name, data in hotel_keys.items()
            if isinstance(data, dict) and not data.get("booking_url")
        ]

    if limit > 0:
        hotels_to_process = hotels_to_process[:limit]

    logger.info("Processing %d hotels...", len(hotels_to_process))

    found_count = 0

    for i, (hotel_name, data) in enumerate(hotels_to_process, 1):
        print(f"\n[{i}/{len(hotels_to_process)}] {hotel_name}")

        # First try direct URL construction (free, no API call)
        print("  Trying direct URL...")
        url = search_booking_url_direct(hotel_name)

        if url:
            print(f"  Found (direct): {url}")
        else:
            # Fall back to Google search
            print("  Searching Google...")
            url = search_booking_url_google(hotel_name, api_key)
            if url:
                print(f"  Found (Google): {url}")
            else:
                print("  Not found")

        if url:
            if hotel_name not in hotel_keys:
                hotel_keys[hotel_name] = {}
            if isinstance(hotel_keys[hotel_name], str):
                hotel_keys[hotel_name] = {"xotelo": hotel_keys[hotel_name]}
            hotel_keys[hotel_name]["booking_url"] = url
            found_count += 1

        # Rate limiting for Google searches
        time.sleep(0.5)

    print(f"\n[DONE] Found {found_count}/{len(hotels_to_process)} Booking URLs")

    return hotel_keys


def main():
    parser = argparse.ArgumentParser(description='Find Booking.com URLs for hotels')
    parser.add_argument('--hotel', type=str, help='Specific hotel name to search')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of hotels')
    parser.add_argument('--dry-run', action='store_true', help='Do not save changes')
    args = parser.parse_args()

    # Check for API key
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        logger.error("SERPAPI_KEY not set. Add it to .env file.")
        sys.exit(1)

    # Load hotel keys
    hotel_keys = load_hotel_keys()
    if not hotel_keys:
        sys.exit(1)

    # Find URLs
    updated_keys = find_booking_urls(
        hotel_keys,
        api_key,
        limit=args.limit,
        specific_hotel=args.hotel
    )

    # Save if not dry run
    if not args.dry_run:
        save_hotel_keys(updated_keys)
    else:
        print("\n[DRY RUN] Changes not saved")


if __name__ == "__main__":
    main()
