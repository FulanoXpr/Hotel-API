# Hotel Price Data Collector

Research tool for collecting hotel pricing data across 149 PRTC-endorsed hotels in Puerto Rico. Supports market analysis, tourism research, and pricing trend studies.

## Overview

The system collects publicly listed hotel rates from multiple sources using a cascade pipeline. If one source has no data, it automatically tries the next until it finds pricing information.

### Data Sources (Cascade Order)

| Source | Description | Free Tier |
|--------|-------------|-----------|
| Xotelo | TripAdvisor aggregated rates | Unlimited |
| SerpApi | Google Hotels search results | 250/month |
| Apify | Booking.com listings | ~1,700/month |
| Amadeus | Global Distribution System (travel agents) | 500/month |

### Coverage

| Metric | Single Source | Cascade Pipeline |
|--------|---------------|------------------|
| Hotels with data | ~95 of 149 | ~145 of 149 |
| Collection rate | ~64% | ~97% |

## Installation

```bash
# Clone repository
git clone <repository-url>
cd Hotel-API

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API keys
cp .env.example .env
```

### API Keys (Optional)

The cascade pipeline works without API keys (Xotelo only), but additional sources require credentials.

**See [API_SETUP.md](API_SETUP.md) for detailed instructions on obtaining each API key (English/Spanish).**

```bash
# .env file
SERPAPI_KEY=your_key              # serpapi.com (100 free/month)
APIFY_TOKEN=your_token            # apify.com ($5 free/month)
AMADEUS_CLIENT_ID=your_id         # developers.amadeus.com (500 free/month)
AMADEUS_CLIENT_SECRET=your_secret
```

## Desktop Application

A graphical interface is available for users who prefer not to use the command line.

### Download

Download the latest release for your platform:

| Platform | Download | Requirements |
|----------|----------|--------------|
| macOS | [HotelPriceChecker.dmg](https://github.com/FulanoXpr/Hotel-API/releases/latest) | macOS 10.13+ |
| Windows | [HotelPriceChecker.zip](https://github.com/FulanoXpr/Hotel-API/releases/latest) | Windows 10+ |

### Installation

#### macOS

1. Download `HotelPriceChecker-macOS.dmg`
2. Open the DMG and drag the app to Applications
3. On first launch, macOS will block the app (unsigned)
4. Go to **System Settings → Privacy & Security** → Click "Open Anyway"

Or remove the quarantine flag via Terminal:
```bash
xattr -cr /Applications/HotelPriceChecker.app
```

#### Windows

1. Download `HotelPriceChecker-Windows.zip`
2. Extract to a folder (e.g., `C:\Program Files\HotelPriceChecker`)
3. Run `HotelPriceChecker.exe`
4. Windows Defender SmartScreen may show a warning (unsigned app)
5. Click "More info" → "Run anyway"

### Features

- Configure API keys with connection testing
- Import hotels from Excel files
- Visual progress tracking with live statistics
- Export results to Excel
- Dark/Light theme support

![Hotel Price Checker](ui/assets/fpr_logo.png)

---

## Command Line Usage

### Basic Data Collection

```bash
# Interactive mode (prompts for dates)
python xotelo_price_updater.py

# Automatic mode (30 days ahead, 1 night)
python xotelo_price_updater.py --auto

# Use all data sources (cascade)
python xotelo_price_updater.py --auto --cascade

# Test with limited hotels
python xotelo_price_updater.py --auto --cascade --limit 10
```

### Additional Tools

```bash
# Retry failed lookups with different dates
python xotelo_price_fixer.py --days-ahead 45 --nights 2

# Find Booking.com URLs for better Apify accuracy
python booking_url_finder.py --limit 50

# Map hotels to Amadeus IDs
python amadeus_id_finder.py

# Web UI for managing hotel keys (port 5000)
python key_manager.py
```

### Running Tests

```bash
# All tests (offline, no API calls)
python -m pytest tests/ -v

# API smoke tests (requires credentials)
RUN_API_SMOKE=1 python -m pytest tests/test_api_smoke.py -v -m smoke
```

## Output

Results are saved to `PRTC_Hotels_Prices_YYYY-MM-DD.xlsx` with these columns:

| Column | Description |
|--------|-------------|
| Snapshot_Date | Date when data was collected |
| Price_USD | Lowest rate found |
| Provider | Source offering the rate |
| Source | Which pipeline source found the data |
| Hotel_Key | Hotel identifier |
| Search_Params | Dates and occupancy used |

## Data Files

| File | Description |
|------|-------------|
| `hotel_keys_db.json` | Hotel mappings (Xotelo keys, Booking URLs, Amadeus IDs) |
| `PRTC Endorsed Hotels (12.25).xlsx` | Source list of PRTC hotels |
| `PRTC_Hotels_Prices_*.xlsx` | Output files with collected data |

## Limitations

- **Advertised rates only**: Prices are publicly listed rates, not negotiated or corporate rates
- **Point-in-time snapshots**: Prices change constantly; results reflect collection moment
- **Amadeus test environment**: Only 21 hotels connected (production requires approval)
- **Small properties**: ~5-10 B&Bs not listed on major platforms may have no data
- **Free tier limits**: Monthly collection is fine; multiple runs may exceed limits
- **Research only**: This tool collects data for analysis, not for booking

## Project Structure

```
Hotel-API/
├── xotelo_price_updater.py    # Main data collection script
├── xotelo_price_fixer.py      # Retry failed lookups
├── booking_url_finder.py      # Map Booking.com URLs
├── amadeus_id_finder.py       # Map Amadeus hotel IDs
├── key_manager.py             # Web UI for hotel keys
├── config.py                  # Environment configuration
├── xotelo_api.py              # Xotelo API client
├── price_providers/           # Cascade pipeline providers
│   ├── base.py                # Provider interface
│   ├── xotelo.py              # TripAdvisor source
│   ├── serpapi.py             # Google Hotels source
│   ├── apify.py               # Booking.com source
│   ├── amadeus.py             # GDS source
│   ├── cascade.py             # Pipeline orchestration
│   └── cache.py               # 24-hour price cache
├── tests/                     # Test suite
├── hotel_keys_db.json         # Hotel mappings database
└── templates/                 # Web UI templates
```

## Scheduling Monthly Collection

### macOS/Linux (cron)

```bash
0 6 1 * * cd /path/to/Hotel-API && python xotelo_price_updater.py --auto --cascade
```

### Windows (Task Scheduler)

Create task with action:
```
python "C:\path\to\Hotel-API\xotelo_price_updater.py" --auto --cascade
```

## Cloud Deployment

For Microsoft Fabric deployment, see [MICROSOFT_FABRIC_GUIDE.md](MICROSOFT_FABRIC_GUIDE.md).

## License

See [LICENSE](LICENSE) file.
