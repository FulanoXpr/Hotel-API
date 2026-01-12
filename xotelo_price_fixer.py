"""
Hotel Price Fixer - Xotelo API
Searches for hotels that didn't match or didn't get prices one by one.
"""

import requests
import openpyxl
from openpyxl.styles import Font, PatternFill
import time
import sys

sys.stdout.reconfigure(line_buffering=True)

# Xotelo API Configuration
BASE_URL = "https://data.xotelo.com/api"

# File paths
INPUT_FILE = "PRTC Endorsed Hotels - Updated Xotelo.xlsx"
OUTPUT_FILE = "PRTC Endorsed Hotels - Updated Xotelo.xlsx"  # Overwrite same file

# Date configuration
CHECK_IN_DATE = "2026-01-30"
CHECK_OUT_DATE = "2026-01-31"

TIMEOUT = 30
REQUEST_DELAY = 1.5


def search_hotel(query):
    """Search for a hotel by name."""
    url = f"{BASE_URL}/search"
    params = {
        "query": query,
        "location_type": "accommodation"
    }
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if data.get('error'):
            return None
        
        result = data.get('result', {})
        hotels = result.get('list', [])
        
        if hotels:
            # Return first result
            hotel = hotels[0]
            return {
                'key': hotel.get('hotel_key', ''),
                'name': hotel.get('name', ''),
                'location': hotel.get('short_place_name', '')
            }
        
        return None
        
    except Exception as e:
        print(f"    [ERROR] Search failed: {e}")
        return None


def get_hotel_rates(hotel_key):
    """Get hotel rates for specific dates."""
    url = f"{BASE_URL}/rates"
    params = {
        "hotel_key": hotel_key,
        "chk_in": CHECK_IN_DATE,
        "chk_out": CHECK_OUT_DATE
    }
    
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
        
        # Get the lowest rate
        lowest_rate = min(rates, key=lambda x: x.get('rate', float('inf')))
        
        return {
            'rate': lowest_rate.get('rate'),
            'provider': lowest_rate.get('name', 'Unknown')
        }
        
    except Exception as e:
        print(f"    [ERROR] Rates failed: {e}")
        return None


def main():
    print("=" * 70)
    print("Hotel Price Fixer - Searching Missing Hotels")
    print("=" * 70)
    
    wb = openpyxl.load_workbook(INPUT_FILE)
    ws = wb.active
    
    # Find column indices
    headers = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}
    
    name_col = 1
    price_col = headers.get('Xotelo_Price_USD')
    provider_col = headers.get('Provider')
    match_col = headers.get('API_Match_Name')
    score_col = headers.get('Match_Score')
    key_col = headers.get('Hotel_Key')
    
    print(f"Columns: price={price_col}, match={match_col}, key={key_col}")
    
    # Collect hotels to process
    no_match = []
    no_price = []
    
    for row in range(2, ws.max_row + 1):
        name = ws.cell(row=row, column=name_col).value
        if not name:
            continue
        
        price = ws.cell(row=row, column=price_col).value if price_col else None
        match = ws.cell(row=row, column=match_col).value if match_col else None
        hotel_key = ws.cell(row=row, column=key_col).value if key_col else None
        
        if not match or match == '':
            no_match.append((row, name))
        elif not price:
            no_price.append((row, name, match, hotel_key))
    
    print(f"\n[INFO] Found {len(no_match)} hotels without match")
    print(f"[INFO] Found {len(no_price)} hotels matched but without price")
    
    updated = 0
    
    # Process hotels without match - search one by one
    print("\n" + "=" * 70)
    print("PART 1: Searching for unmatched hotels")
    print("=" * 70)
    
    for idx, (row, name) in enumerate(no_match, 1):
        print(f"\n[{idx}/{len(no_match)}] Searching: {name}")
        
        # Try different search variations
        search_terms = [
            name,
            name.replace('(', '').replace(')', ''),
            name.split('(')[0].strip(),
            ' '.join(name.split()[:3])  # First 3 words
        ]
        
        found = None
        for term in search_terms:
            if len(term) < 5:
                continue
            result = search_hotel(term)
            if result:
                # Check if it's in Puerto Rico
                location = result.get('location', '').lower()
                if 'puerto rico' in location or 'pr' in location:
                    found = result
                    print(f"  -> Found: {result['name']} ({result['location']})")
                    break
            time.sleep(0.5)
        
        if found:
            # Get price
            print(f"  -> Getting price...")
            rate_data = get_hotel_rates(found['key'])
            
            if rate_data:
                print(f"  -> Price: ${rate_data['rate']} ({rate_data['provider']})")
                ws.cell(row=row, column=price_col, value=rate_data['rate'])
                ws.cell(row=row, column=provider_col, value=rate_data['provider'])
                updated += 1
            else:
                print(f"  -> No price available")
                ws.cell(row=row, column=provider_col, value="No price")
            
            ws.cell(row=row, column=match_col, value=found['name'])
            ws.cell(row=row, column=score_col, value="SEARCH")
            ws.cell(row=row, column=key_col, value=found['key'])
        else:
            print(f"  -> NOT FOUND in Puerto Rico")
            ws.cell(row=row, column=provider_col, value="Not found")
        
        time.sleep(REQUEST_DELAY)
    
    # Process hotels with match but no price - retry getting prices
    print("\n" + "=" * 70)
    print("PART 2: Retrying prices for matched hotels")
    print("=" * 70)
    
    for idx, (row, name, match, hotel_key) in enumerate(no_price, 1):
        print(f"\n[{idx}/{len(no_price)}] Retrying: {name}")
        print(f"  -> Key: {hotel_key}")
        
        if hotel_key:
            rate_data = get_hotel_rates(hotel_key)
            
            if rate_data:
                print(f"  -> Price: ${rate_data['rate']} ({rate_data['provider']})")
                ws.cell(row=row, column=price_col, value=rate_data['rate'])
                ws.cell(row=row, column=provider_col, value=rate_data['provider'])
                updated += 1
            else:
                print(f"  -> Still no price")
                ws.cell(row=row, column=provider_col, value="No price available")
        else:
            print(f"  -> No hotel key to retry")
        
        time.sleep(REQUEST_DELAY)
    
    # Save
    wb.save(OUTPUT_FILE)
    print("\n" + "=" * 70)
    print(f"[COMPLETE] Updated {updated} hotels with new prices")
    print(f"[SAVED] {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
