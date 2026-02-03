# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hotel Price Updater for Puerto Rico Tourism Company (PRTC). Fetches real-time prices for 149 endorsed hotels using a cascade of APIs: Xotelo (TripAdvisor), SerpApi (Google Hotels), and Apify (Booking.com).

## Commands

```bash
# Install all dependencies
pip install requests openpyxl flask google-search-results apify-client python-dotenv pytest

# Main price updater
python xotelo_price_updater.py                          # Interactive mode
python xotelo_price_updater.py --auto                   # Automatic (+30 days)
python xotelo_price_updater.py --auto --multi-date      # Try multiple dates
python xotelo_price_updater.py --auto --cascade         # Use all price sources
python xotelo_price_updater.py --auto --cascade --limit 10  # Test with few hotels

# Find Booking.com URLs (improves Apify accuracy)
python booking_url_finder.py --limit 50

# Run tests
python -m pytest tests/ -v                              # All tests (no network)
python -m pytest tests/ -v -k "test_xotelo"             # Single test file
RUN_API_SMOKE=1 python -m pytest tests/test_api_smoke.py -v  # API smoke tests
```

## Architecture

```
PRTC Excel → hotel_keys_db.json (lookup) → Cascade Pipeline → Updated Excel

Cascade Pipeline (--cascade):
  1. Cache (24h TTL)
  2. Xotelo (free, ~64% coverage)
  3. SerpApi (Google Hotels, 250/month free)
  4. Apify (Booking.com, $5/month free)
```

**Core Modules:**
- `xotelo_api.py` - `XoteloAPI` class with `/rates`, `/search`, `/list` endpoints. Use `get_client()` for singleton. Always call `api.wait()` between requests.
- `config.py` - Environment variables with defaults. Loads `.env` if present.
- `price_providers/` - Cascade pipeline: `XoteloProvider`, `SerpApiProvider`, `ApifyProvider`, `CascadePriceProvider`, `PriceCache`

**Scripts:**
- `xotelo_price_updater.py` - Main CLI tool
- `booking_url_finder.py` - Populate Booking.com URLs in hotel_keys_db.json
- `key_manager.py` - Flask web UI for hotel key management (port 5000)
- `xotelo_price_fixer.py` - Retry failed lookups with custom dates

## Key Data Formats

**hotel_keys_db.json** (supports both formats):
```json
{
  "Hotel A": "g147319-d123",
  "Hotel B": {"xotelo": "g147319-d456", "booking_url": "https://www.booking.com/hotel/pr/..."}
}
```

**Output Excel columns:** `Snapshot_Date`, `Price_USD`, `Provider`, `Hotel_Key`, `Search_Params`, `Source`

## API Configuration

```bash
# .env file for cascade mode
SERPAPI_KEY=your_key      # serpapi.com (250 free/month)
APIFY_TOKEN=your_token    # apify.com ($5 free/month)
CASCADE_ENABLED=true
CACHE_TTL_HOURS=24
```

## Notes

- UI prompts are in Spanish
- Default search: +30 days, 1 night, 1 room, 2 adults
- Rate limiting: 0.5s between Xotelo requests (`REQUEST_DELAY` env var)
- Xotelo keys format: `g{location}-d{hotel_id}` (e.g., `g147319-d1837036`)
