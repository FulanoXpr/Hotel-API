"""
Extract All Hotels from Puerto Rico - Xotelo API
Extracts all 1108 hotels with their Key and TripAdvisor URL.
"""

import requests
import json
import time
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

# Force immediate output
sys.stdout.reconfigure(line_buffering=True)

# Xotelo API Configuration
BASE_URL = "https://data.xotelo.com/api"
LOCATION_KEY = "g147319"  # Puerto Rico (entire island)

# Output files
OUTPUT_JSON = "all_hotels_puerto_rico.json"
OUTPUT_EXCEL = "all_hotels_puerto_rico.xlsx"

# Request configuration
TIMEOUT = 30
REQUEST_DELAY = 1  # Seconds between API calls


def get_hotel_list(location_key, limit=100, offset=0):
    """Get list of hotels in Puerto Rico."""
    
    url = f"{BASE_URL}/list"
    params = {
        "location_key": location_key,
        "limit": limit,
        "offset": offset,
        "sort": "best_value"
    }
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if data.get('error'):
            print(f"  [ERROR] API returned error: {data['error']}")
            return [], 0
        
        result = data.get('result', {})
        hotels = result.get('list', [])
        total_count = result.get('total_count', 0)
        
        return hotels, total_count
        
    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] Request timed out")
        return [], 0
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Request failed: {e}")
        return [], 0


def main():
    """Main execution function."""
    print("=" * 70)
    print("Extract All Hotels from Puerto Rico - Xotelo API")
    print("=" * 70)
    print(f"Location: Puerto Rico (entire island)")
    print("=" * 70)
    
    # Get all hotels from Puerto Rico (paginated)
    print("\n[STEP 1] Fetching ALL hotels from Puerto Rico...")
    all_hotels = []
    offset = 0
    limit = 100
    total_count = 0
    
    while True:
        print(f"  [FETCH] Getting hotels {offset + 1} to {offset + limit}...")
        hotels, total = get_hotel_list(LOCATION_KEY, limit=limit, offset=offset)
        
        if total > 0:
            total_count = total
        
        if not hotels:
            if offset == 0:
                print("[ERROR] No hotels found from API. Exiting.")
                return
            break
        
        all_hotels.extend(hotels)
        offset += limit
        
        print(f"  [PROGRESS] Collected {len(all_hotels)}/{total_count} hotels")
        
        # Check if we've collected all hotels
        if offset >= total_count:
            print(f"  [DONE] All {total_count} hotels collected!")
            break
        
        time.sleep(REQUEST_DELAY)
    
    print(f"\n[INFO] Total hotels collected: {len(all_hotels)}")
    
    # Extract relevant data
    print("\n[STEP 2] Extracting Key and URL data...")
    hotel_data = []
    for hotel in all_hotels:
        hotel_data.append({
            "name": hotel.get("name", ""),
            "key": hotel.get("key", ""),
            "url": hotel.get("url", ""),
            "accommodation_type": hotel.get("accommodation_type", ""),
            "rating": hotel.get("review_summary", {}).get("rating") if hotel.get("review_summary") else None,
            "review_count": hotel.get("review_summary", {}).get("count") if hotel.get("review_summary") else None
        })
    
    # Save to JSON
    print(f"\n[STEP 3] Saving to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(hotel_data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] Saved {len(hotel_data)} hotels to JSON")
    
    # Save to Excel
    print(f"\n[STEP 4] Saving to {OUTPUT_EXCEL}...")
    wb = Workbook()
    ws = wb.active
    ws.title = "Hotels Puerto Rico"
    
    # Header styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    # Headers
    headers = ["#", "Hotel Name", "Key", "URL", "Type", "Rating", "Reviews"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Data rows
    for idx, hotel in enumerate(hotel_data, 1):
        ws.cell(row=idx + 1, column=1, value=idx)
        ws.cell(row=idx + 1, column=2, value=hotel["name"])
        ws.cell(row=idx + 1, column=3, value=hotel["key"])
        ws.cell(row=idx + 1, column=4, value=hotel["url"])
        ws.cell(row=idx + 1, column=5, value=hotel["accommodation_type"])
        ws.cell(row=idx + 1, column=6, value=hotel["rating"])
        ws.cell(row=idx + 1, column=7, value=hotel["review_count"])
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 50
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 80
    ws.column_dimensions['E'].width = 20
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 10
    
    wb.save(OUTPUT_EXCEL)
    print(f"  [OK] Saved {len(hotel_data)} hotels to Excel")
    
    # Summary
    print("\n" + "=" * 70)
    print("[COMPLETE] Extraction finished!")
    print(f"  - Total hotels: {len(hotel_data)}")
    print(f"  - JSON file: {OUTPUT_JSON}")
    print(f"  - Excel file: {OUTPUT_EXCEL}")
    print("=" * 70)
    
    # Show first 5 hotels as sample
    print("\n[SAMPLE] First 5 hotels:")
    for i, hotel in enumerate(hotel_data[:5], 1):
        print(f"  {i}. {hotel['name']}")
        print(f"     Key: {hotel['key']}")
        print(f"     URL: {hotel['url'][:60]}..." if len(hotel['url']) > 60 else f"     URL: {hotel['url']}")


if __name__ == "__main__":
    main()
