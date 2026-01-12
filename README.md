# Hotel Price Updater API

Automated system for fetching and updating hotel prices in Puerto Rico using the **Xotelo API** (TripAdvisor-based). Uses pre-mapped hotel keys for fast and accurate price lookups.

## 📋 Project Overview

The system processes Excel files containing PRTC endorsed hotels and retrieves real-time prices using direct Xotelo hotel keys.

### Key Features
*   **Key-Based Lookups:** Uses pre-mapped Xotelo keys for 149 PRTC hotels (no fuzzy matching needed)
*   **Automatic Mode:** `--auto` flag for scheduled monthly automation
*   **Snapshot Tracking:** Records collection date for historical analysis
*   **Multi-Provider:** Retrieves lowest rate from Booking.com, Agoda, Trip.com, etc.
*   **Interactive Mode:** Prompts for custom dates, rooms, and guests

## 🚀 Main Scripts

### `xotelo_price_updater.py` - Primary Tool
The main price updater with two modes:

```bash
# Interactive mode (prompts for dates/rooms/guests)
python xotelo_price_updater.py

# Automatic mode (uses defaults, no prompts)
python xotelo_price_updater.py --auto
```

**Default parameters (auto mode):**
- Check-in: +30 days from today
- Check-out: +31 days (1 night stay)
- Rooms: 1
- Adults per room: 2

### `extract_all_hotels.py`
Extracts all hotels from Puerto Rico via Xotelo API for key mapping.

### `key_manager.py`
Web interface for managing hotel-to-key mappings in `hotel_keys_db.json`.

### `xotelo_price_fixer.py`
Utility for deep searches and retries on unmatched hotels.

## 📁 Data Files

| File | Description |
|------|-------------|
| `hotel_keys_db.json` | Database mapping 149 hotel names to Xotelo keys |
| `PRTC Endorsed Hotels (12.25).xlsx` | Source list of PRTC endorsed hotels |
| `PRTC_Hotels_Prices_YYYY-MM-DD.xlsx` | Output with prices and snapshot date |

## 🛠️ Installation & Setup

1. Ensure Python 3.8+ is installed
2. Install dependencies:
   ```bash
   pip install requests openpyxl pandas
   ```
3. Place source file `PRTC Endorsed Hotels (12.25).xlsx` in root directory

## ⏰ Monthly Automation (Windows)

To schedule automatic monthly runs:

1. Open Task Scheduler
2. Create new task with action:
   ```
   python "C:\path\to\Hotel API\xotelo_price_updater.py" --auto
   ```
3. Set trigger for monthly schedule

## 📊 Output Columns

The system adds these columns to the output Excel:

| Column | Description |
|--------|-------------|
| `Snapshot_Date` | Date when prices were collected |
| `Xotelo_Price_USD` | Lowest retrieved nightly rate |
| `Provider` | Booking site offering the rate |
| `Hotel_Key` | Xotelo hotel identifier |
| `Search_Params` | Dates and occupancy used for search |

## ☁️ Microsoft Fabric Deployment

For cloud deployment instructions, see:
👉 **[Microsoft Fabric Migration Guide](MICROSOFT_FABRIC_GUIDE.md)**