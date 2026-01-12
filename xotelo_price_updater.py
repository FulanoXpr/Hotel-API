"""
Hotel Price Updater - Xotelo API
Fetches hotel prices from Xotelo (TripAdvisor-based) and updates the PRTC Endorsed Hotels Excel file.
Free API with no authentication required.
"""

import requests
import openpyxl
from openpyxl.styles import Font, PatternFill
from difflib import SequenceMatcher
import time
import re

# Xotelo API Configuration
BASE_URL = "https://data.xotelo.com/api"
LOCATION_KEY = "g147319"  # Puerto Rico (entire island)

# File paths
EXCEL_FILE = "PRTC Endorsed Hotels (12.25).xlsx"
OUTPUT_FILE = "PRTC Endorsed Hotels - Updated Xotelo.xlsx"

# Date configuration
CHECK_IN_DATE = "2026-01-30"
CHECK_OUT_DATE = "2026-01-31"

# Request timeout and rate limiting
TIMEOUT = 30
REQUEST_DELAY = 1  # Seconds between API calls (reduced for speed)

# Force immediate output
import sys
sys.stdout.reconfigure(line_buffering=True)


def get_hotel_list(location_key, limit=100, offset=0):
    """Get list of hotels in Puerto Rico."""
    print(f"[LIST] Fetching hotels from Puerto Rico (offset: {offset}, limit: {limit})...")
    
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
            return []
        
        result = data.get('result', {})
        hotels = result.get('list', [])
        total_count = result.get('total_count', 0)
        
        print(f"  [OK] Found {len(hotels)} hotels (total available: {total_count})")
        
        return hotels, total_count
        
    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] Request timed out")
        return [], 0
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Request failed: {e}")
        return [], 0


def get_hotel_rates(hotel_key, chk_in, chk_out, retries=2):
    """Get hotel rates for specific dates."""
    
    url = f"{BASE_URL}/rates"
    params = {
        "hotel_key": hotel_key,
        "chk_in": chk_in,
        "chk_out": chk_out
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error'):
                return None
            
            result = data.get('result', {})
            rates = result.get('rates', [])
            
            if not rates:
                return None
            
            # Get the lowest rate from all providers
            lowest_rate = min(rates, key=lambda x: x.get('rate', float('inf')))
            
            return {
                'rate': lowest_rate.get('rate'),
                'provider': lowest_rate.get('name', 'Unknown'),
                'code': lowest_rate.get('code', '')
            }
            
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None
        except requests.exceptions.RequestException:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None
    
    return None


def normalize_name(name):
    """Normalize hotel name for better matching."""
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common words
    remove_words = ['hotel', 'resort', 'inn', 'suites', 'the', 'and', '&', 'de', 'del', 'la', 'el']
    for word in remove_words:
        name = re.sub(r'\b' + word + r'\b', '', name)
    
    # Remove special characters and extra spaces
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def similarity_ratio(a, b):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def find_best_match(excel_name, api_hotels, threshold=0.6):
    """Find the best matching hotel from API results."""
    best_match = None
    best_score = 0
    
    for hotel in api_hotels:
        api_name = hotel.get('name', '')
        score = similarity_ratio(excel_name, api_name)
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = hotel
    
    return best_match, best_score


def update_excel_with_prices(excel_hotels_with_prices):
    """Read Excel, and update with prices."""
    print("\n[EXCEL] Updating Excel file...")
    
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # Find the last column with data and add new columns
    max_col = ws.max_column
    price_col = max_col + 1
    provider_col = max_col + 2
    match_col = max_col + 3
    score_col = max_col + 4
    key_col = max_col + 5
    
    # Add headers with styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    headers = [
        (price_col, "Xotelo_Price_USD"),
        (provider_col, "Provider"),
        (match_col, "API_Match_Name"),
        (score_col, "Match_Score"),
        (key_col, "Hotel_Key")
    ]
    
    for col, header_text in headers:
        cell = ws.cell(row=1, column=col, value=header_text)
        cell.fill = header_fill
        cell.font = header_font
    
    # Update rows with matched data
    for row_num, hotel_data in excel_hotels_with_prices.items():
        ws.cell(row=row_num, column=price_col, value=hotel_data.get('price'))
        ws.cell(row=row_num, column=provider_col, value=hotel_data.get('provider'))
        ws.cell(row=row_num, column=match_col, value=hotel_data.get('api_name'))
        ws.cell(row=row_num, column=score_col, value=hotel_data.get('score'))
        ws.cell(row=row_num, column=key_col, value=hotel_data.get('hotel_key'))
    
    # Save the updated workbook
    wb.save(OUTPUT_FILE)
    print(f"\n[SAVE] Saved to: {OUTPUT_FILE}")
    
    return True


def main():
    """Main execution function."""
    print("=" * 70)
    print("Hotel Price Updater - Xotelo API (TripAdvisor-based)")
    print("=" * 70)
    print(f"Location: Puerto Rico (entire island)")
    print(f"Check-in: {CHECK_IN_DATE}")
    print(f"Check-out: {CHECK_OUT_DATE}")
    print("=" * 70)
    
    # Step 1: Get all hotels from Puerto Rico (paginated)
    print("\n[STEP 1] Fetching hotels from Puerto Rico...")
    all_api_hotels = []
    offset = 0
    limit = 100
    
    while True:
        hotels, total_count = get_hotel_list(LOCATION_KEY, limit=limit, offset=offset)
        
        if not hotels:
            break
        
        all_api_hotels.extend(hotels)
        offset += limit
        
        print(f"  [PROGRESS] Collected {len(all_api_hotels)}/{total_count} hotels")
        
        # Limit to 500 hotels as per user's suggestion
        if len(all_api_hotels) >= 500 or offset >= total_count:
            break
        
        time.sleep(REQUEST_DELAY)
    
    print(f"\n[INFO] Total API hotels collected: {len(all_api_hotels)}")
    
    if not all_api_hotels:
        print("[ERROR] No hotels found from API. Exiting.")
        return
    
    # Step 2: Load Excel and match hotels
    print("\n[STEP 2] Loading Excel and matching hotels...")
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    excel_hotels_with_prices = {}
    hotels_matched = 0
    hotels_with_prices = 0
    hotels_total = 0
    
    for row in range(2, ws.max_row + 1):
        hotel_name = ws.cell(row=row, column=1).value
        
        if not hotel_name:
            continue
        
        hotels_total += 1
        
        # Find matching hotel in API results
        match, score = find_best_match(hotel_name, all_api_hotels)
        
        if match:
            hotels_matched += 1
            hotel_key = match.get('key', '')
            api_name = match.get('name', '')
            
            print(f"\n[MATCH {hotels_matched}] {hotel_name}")
            print(f"  → {api_name} (Score: {score:.0%})")
            print(f"  → Key: {hotel_key}")
            
            # Get price for this hotel
            if hotel_key:
                print(f"  → Fetching price...")
                rate_data = get_hotel_rates(hotel_key, CHECK_IN_DATE, CHECK_OUT_DATE)
                
                if rate_data:
                    price = rate_data['rate']
                    provider = rate_data['provider']
                    print(f"  → Price: ${price:.2f} ({provider})")
                    
                    excel_hotels_with_prices[row] = {
                        'price': price,
                        'provider': provider,
                        'api_name': api_name,
                        'score': f"{score:.0%}",
                        'hotel_key': hotel_key
                    }
                    hotels_with_prices += 1
                else:
                    print(f"  → No price available")
                    excel_hotels_with_prices[row] = {
                        'price': None,
                        'provider': 'N/A',
                        'api_name': api_name,
                        'score': f"{score:.0%}",
                        'hotel_key': hotel_key
                    }
                
                time.sleep(REQUEST_DELAY)
    
    print(f"\n[STATS] Matched {hotels_matched}/{hotels_total} hotels")
    print(f"[STATS] Got prices for {hotels_with_prices}/{hotels_matched} matched hotels")
    
    # Step 3: Update Excel
    if excel_hotels_with_prices:
        update_excel_with_prices(excel_hotels_with_prices)
        print("\n" + "=" * 70)
        print("[COMPLETE]")
        print(f"[RESULTS] {hotels_with_prices} hotels updated with prices")
        print(f"[RESULTS] {hotels_matched - hotels_with_prices} hotels matched but no price")
        print(f"[RESULTS] {hotels_total - hotels_matched} hotels not matched")
        print("=" * 70)
    else:
        print("\n[WARN] No hotels matched or priced")


if __name__ == "__main__":
    main()
