# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hotel Price Updater for Puerto Rico Tourism Company (PRTC) hotels. Fetches real-time prices from Xotelo API (TripAdvisor-based) using pre-mapped hotel keys for 149 endorsed hotels.

## Commands

```bash
# Install dependencies
pip install requests openpyxl pandas flask

# Install dev dependencies (for testing)
pip install pytest pytest-cov

# Main price updater - interactive mode (prompts for dates)
python xotelo_price_updater.py

# Main price updater - automatic mode (30 days ahead, no prompts)
python xotelo_price_updater.py --auto

# Multi-date mode (fetches prices for multiple dates)
python xotelo_price_updater.py --multi-date

# Web UI for managing hotel-to-key mappings (Flask on port 5000)
python key_manager.py

# Extract all Puerto Rico hotels from Xotelo API
python extract_all_hotels.py

# Retry unmatched/unpriced hotels (uses relative dates by default)
python xotelo_price_fixer.py
python xotelo_price_fixer.py --days-ahead 45 --nights 2
python xotelo_price_fixer.py --check-in 2026-03-15 --check-out 2026-03-16
python xotelo_price_fixer.py --input "archivo.xlsx" --output "salida.xlsx"

# Run all tests
python -m pytest tests/ -v

# Run unit/integration tests only (fast, no network)
python -m pytest tests/ -v --ignore=tests/test_api_smoke.py

# Run smoke tests only (hits real API, requires RUN_API_SMOKE=1)
RUN_API_SMOKE=1 python -m pytest tests/test_api_smoke.py -v -m smoke
```

## Architecture

**Core Data Flow:**
```
PRTC Excel → hotel_keys_db.json (lookup) → Xotelo API /rates → Updated Excel with prices
```

**Shared Modules:**
- `xotelo_api.py` - `XoteloAPI` class with typed methods for `/rates`, `/search`, `/list` endpoints. Handles retry logic, rate limiting via `api.wait()`, and request timeouts. Use `get_client()` for singleton access.
- `config.py` - Centralized configuration via environment variables with defaults (BASE_URL, TIMEOUT, REQUEST_DELAY, file paths, search parameters)

**Scripts:**
- `xotelo_price_updater.py` - Main tool: reads Excel, looks up keys, calls API, writes dated output
- `key_manager.py` - Flask web UI for managing hotel key mappings
- `extract_all_hotels.py` - Bulk extraction of all PR hotels from API
- `xotelo_price_fixer.py` - Retry tool for failed lookups with CLI args for dates and files

**Key Data Files:**
- `hotel_keys_db.json` - Maps hotel names → Xotelo keys (e.g., `"Hotel Name": "g147319-d1234567"`)
- `PRTC Endorsed Hotels (12.25).xlsx` - Source hotel list (column 1)
- `PRTC_Hotels_Prices_YYYY-MM-DD.xlsx` - Output with prices and snapshot date

## API Details

**Xotelo API** (`https://data.xotelo.com/api`):
- `/list` - Get hotels by location
- `/search` - Search hotels by name
- `/rates` - Get pricing (requires hotel key + dates)

**Rate Limiting:** 0.5s delay between requests (configurable via `REQUEST_DELAY` env var). Timeout: 30s with 2 retries. Always call `api.wait()` between hotel requests.

## Output Columns

The price updater adds these columns: `Snapshot_Date`, `Xotelo_Price_USD`, `Provider`, `Hotel_Key`, `Search_Params`

## Notes

- UI prompts are in Spanish
- Default auto-mode search: +30 days check-in, 1 night, 1 room, 2 adults
- For cloud deployment, see `MICROSOFT_FABRIC_GUIDE.md`
