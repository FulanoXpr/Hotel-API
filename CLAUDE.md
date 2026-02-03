# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hotel Price Updater for Puerto Rico Tourism Company (PRTC). Fetches real-time prices for 149 endorsed hotels using a cascade of APIs: Xotelo (TripAdvisor), SerpApi (Google Hotels), and Apify (Booking.com).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt           # Production only
pip install -r requirements-dev.txt       # With pytest

# Main price updater
python xotelo_price_updater.py                          # Interactive mode
python xotelo_price_updater.py --auto                   # Automatic (+30 days)
python xotelo_price_updater.py --auto --multi-date      # Try multiple dates
python xotelo_price_updater.py --auto --cascade         # Use all price sources
python xotelo_price_updater.py --auto --cascade --limit 10  # Test with few hotels

# Price fixer (retry failed lookups)
python xotelo_price_fixer.py --days-ahead 45 --nights 2           # Relative dates
python xotelo_price_fixer.py --check-in 2026-03-15 --check-out 2026-03-16  # Explicit dates
python xotelo_price_fixer.py --input "archivo.xlsx" --output "salida.xlsx"

# Find Booking.com URLs (improves Apify accuracy)
python booking_url_finder.py --limit 50

# Run tests
python -m pytest tests/ -v                              # All tests (no network)
python -m pytest tests/ -v -k "test_xotelo"             # Single test file
python -m pytest tests/test_config.py::test_defaults -v # Single test function
RUN_API_SMOKE=1 python -m pytest tests/test_api_smoke.py -v -m smoke  # API smoke tests
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
- `xotelo_api.py` - `XoteloAPI` class with `/rates`, `/search`, `/list` endpoints. Use `get_client()` for singleton. Always call `api.wait()` between requests. Filters invalid rates (non-numeric or `None`) before returning minimum.
- `config.py` - Environment variables with defaults. Loads `.env` if present. All settings are `Final` typed.
- `price_providers/` - Cascade pipeline package:
  - `base.py` - `PriceProvider` ABC and `PriceResult` dataclass
  - `xotelo.py`, `serpapi.py`, `apify.py` - Individual provider implementations
  - `cascade.py` - `CascadePriceProvider` orchestrates fallback order
  - `cache.py` - `PriceCache` with configurable TTL

**Scripts:**
- `xotelo_price_updater.py` - Main CLI tool. Calls `api.wait()` after each hotel, including in `--multi-date` mode.
- `booking_url_finder.py` - Populate Booking.com URLs in hotel_keys_db.json
- `key_manager.py` - Flask web UI for hotel key management (port 5000)
- `xotelo_price_fixer.py` - Retry failed lookups. Supports `--check-in/--check-out` or `--days-ahead/--nights` for flexible date handling.

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

## Testing Notes

- Tests use markers: `smoke` for API tests requiring network
- Smoke tests are excluded by default; run with `-m smoke` and `RUN_API_SMOKE=1`
- All other tests are fully offline with mocked responses

## Notes

- UI prompts are in Spanish
- Default search: +30 days, 1 night, 1 room, 2 adults
- Rate limiting: 0.5s between Xotelo requests (`REQUEST_DELAY` env var)
- Xotelo keys format: `g{location}-d{hotel_id}` (e.g., `g147319-d1837036`)
- Microsoft Fabric deployment: see `MICROSOFT_FABRIC_GUIDE.md`
