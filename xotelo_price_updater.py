"""
Hotel Price Updater - Xotelo API (Key-Based)
Fetches hotel prices from Xotelo using direct hotel keys from hotel_keys_db.json.
Supports both interactive and automatic modes for monthly automation.

Usage:
  Interactive:  python xotelo_price_updater.py
  Automatic:    python xotelo_price_updater.py --auto
"""

import requests
import openpyxl
from openpyxl.styles import Font, PatternFill
import time
import json
import os
import sys
import argparse
from datetime import datetime, timedelta

# Xotelo API Configuration
BASE_URL = "https://data.xotelo.com/api"

# File paths
EXCEL_FILE = "PRTC Endorsed Hotels (12.25).xlsx"
HOTEL_KEYS_DB = "hotel_keys_db.json"

# Default search parameters (for automatic mode)
DEFAULT_DAYS_AHEAD = 30  # Check-in date: 30 days from today
DEFAULT_NIGHTS = 1
DEFAULT_ROOMS = 1
DEFAULT_ADULTS = 2

# Request timeout and rate limiting
TIMEOUT = 30
REQUEST_DELAY = 0.5

# Force immediate output
sys.stdout.reconfigure(line_buffering=True)


def get_user_input():
    """Get search parameters from user (interactive mode)."""
    print("\n" + "=" * 70)
    print("CONFIGURACIÓN DE BÚSQUEDA")
    print("=" * 70)
    
    # Get check-in date
    while True:
        default_date = (datetime.now() + timedelta(days=DEFAULT_DAYS_AHEAD)).strftime("%Y-%m-%d")
        print(f"\n📅 Fecha de Check-in (YYYY-MM-DD) [default: {default_date}]: ", end="")
        chk_in = input().strip()
        if not chk_in:
            chk_in = default_date
        
        try:
            check_in_date = datetime.strptime(chk_in, "%Y-%m-%d")
            if check_in_date < datetime.now():
                print("   ⚠️  La fecha debe ser en el futuro. Intenta de nuevo.")
                continue
            break
        except ValueError:
            print("   ⚠️  Formato inválido. Usa YYYY-MM-DD (ej: 2026-02-15)")
    
    # Get check-out date
    while True:
        default_checkout = (check_in_date + timedelta(days=DEFAULT_NIGHTS)).strftime("%Y-%m-%d")
        print(f"\n📅 Fecha de Check-out (YYYY-MM-DD) [default: {default_checkout}]: ", end="")
        chk_out = input().strip()
        if not chk_out:
            chk_out = default_checkout
        
        try:
            check_out_date = datetime.strptime(chk_out, "%Y-%m-%d")
            if check_out_date <= check_in_date:
                print("   ⚠️  Check-out debe ser después de check-in. Intenta de nuevo.")
                continue
            break
        except ValueError:
            print("   ⚠️  Formato inválido. Usa YYYY-MM-DD (ej: 2026-02-16)")
    
    # Get number of rooms
    while True:
        print(f"\n🛏️  Número de habitaciones (1-8) [default: {DEFAULT_ROOMS}]: ", end="")
        rooms_input = input().strip()
        if not rooms_input:
            rooms = DEFAULT_ROOMS
            break
        try:
            rooms = int(rooms_input)
            if 1 <= rooms <= 8:
                break
            print("   ⚠️  Debe ser entre 1 y 8 habitaciones.")
        except ValueError:
            print("   ⚠️  Por favor ingresa un número válido.")
    
    # Get number of adults per room
    while True:
        print(f"\n👥 Adultos por habitación (1-4) [default: {DEFAULT_ADULTS}]: ", end="")
        adults_input = input().strip()
        if not adults_input:
            adults = DEFAULT_ADULTS
            break
        try:
            adults = int(adults_input)
            if 1 <= adults <= 4:
                break
            print("   ⚠️  Debe ser entre 1 y 4 adultos por habitación.")
        except ValueError:
            print("   ⚠️  Por favor ingresa un número válido.")
    
    nights = (check_out_date - check_in_date).days
    
    print("\n" + "-" * 70)
    print("📋 RESUMEN DE BÚSQUEDA:")
    print(f"   • Check-in:    {chk_in}")
    print(f"   • Check-out:   {chk_out}")
    print(f"   • Noches:      {nights}")
    print(f"   • Habitaciones: {rooms}")
    print(f"   • Adultos/hab: {adults}")
    print("-" * 70)
    
    print("\n¿Continuar con esta búsqueda? (S/n): ", end="")
    confirm = input().strip().lower()
    if confirm == 'n':
        print("\n❌ Búsqueda cancelada.")
        return None
    
    return {
        'chk_in': chk_in,
        'chk_out': chk_out,
        'rooms': rooms,
        'adults': adults,
        'nights': nights
    }


def get_auto_params():
    """Get default parameters for automatic mode."""
    today = datetime.now()
    check_in = today + timedelta(days=DEFAULT_DAYS_AHEAD)
    check_out = check_in + timedelta(days=DEFAULT_NIGHTS)
    
    return {
        'chk_in': check_in.strftime("%Y-%m-%d"),
        'chk_out': check_out.strftime("%Y-%m-%d"),
        'rooms': DEFAULT_ROOMS,
        'adults': DEFAULT_ADULTS,
        'nights': DEFAULT_NIGHTS
    }


def load_hotel_keys():
    """Load hotel name to key mappings from JSON database."""
    if not os.path.exists(HOTEL_KEYS_DB):
        print(f"[ERROR] Hotel keys database not found: {HOTEL_KEYS_DB}")
        return {}
    
    try:
        with open(HOTEL_KEYS_DB, 'r', encoding='utf-8') as f:
            keys = json.load(f)
        print(f"[INFO] Loaded {len(keys)} hotel keys from {HOTEL_KEYS_DB}")
        return keys
    except Exception as e:
        print(f"[ERROR] Failed to load hotel keys: {e}")
        return {}


def get_hotel_rates(hotel_key, chk_in, chk_out, rooms=1, adults=2, retries=2):
    """Get hotel rates for specific dates and occupancy."""
    
    url = f"{BASE_URL}/rates"
    params = {
        "hotel_key": hotel_key,
        "chk_in": chk_in,
        "chk_out": chk_out,
        "rooms": rooms,
        "adults": adults
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


def update_excel_with_prices(excel_hotels_with_prices, search_params, snapshot_date):
    """Read Excel and update with prices, including snapshot date."""
    print("\n[EXCEL] Updating Excel file...")
    
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # Find the last column with data and add new columns
    max_col = ws.max_column
    snapshot_col = max_col + 1
    price_col = max_col + 2
    provider_col = max_col + 3
    key_col = max_col + 4
    search_col = max_col + 5
    
    # Add headers with styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    headers = [
        (snapshot_col, "Snapshot_Date"),
        (price_col, "Xotelo_Price_USD"),
        (provider_col, "Provider"),
        (key_col, "Hotel_Key"),
        (search_col, "Search_Params")
    ]
    
    for col, header_text in headers:
        cell = ws.cell(row=1, column=col, value=header_text)
        cell.fill = header_fill
        cell.font = header_font
    
    # Create search info string
    search_info = f"{search_params['chk_in']} to {search_params['chk_out']} | {search_params['rooms']}rm/{search_params['adults']}ad"
    
    # Update rows with matched data
    for row_num, hotel_data in excel_hotels_with_prices.items():
        ws.cell(row=row_num, column=snapshot_col, value=snapshot_date)
        ws.cell(row=row_num, column=price_col, value=hotel_data.get('price'))
        ws.cell(row=row_num, column=provider_col, value=hotel_data.get('provider'))
        ws.cell(row=row_num, column=key_col, value=hotel_data.get('hotel_key'))
        ws.cell(row=row_num, column=search_col, value=search_info)
    
    # Generate output filename with date
    output_file = f"PRTC_Hotels_Prices_{snapshot_date}.xlsx"
    wb.save(output_file)
    print(f"\n[SAVE] Saved to: {output_file}")
    
    return output_file


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hotel Price Updater - Xotelo API')
    parser.add_argument('--auto', action='store_true', 
                        help='Run in automatic mode with default parameters (no prompts)')
    args = parser.parse_args()
    
    # Get snapshot date (when the data was collected)
    snapshot_date = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 70)
    print("🏨 Hotel Price Updater - Xotelo API (Key-Based)")
    print("=" * 70)
    print(f"📸 Snapshot Date: {snapshot_date}")
    
    if args.auto:
        print("🤖 Mode: AUTOMATIC (using default parameters)")
        search_params = get_auto_params()
        print(f"   Check-in:  {search_params['chk_in']} (+{DEFAULT_DAYS_AHEAD} days)")
        print(f"   Check-out: {search_params['chk_out']}")
        print(f"   Rooms: {search_params['rooms']}, Adults/room: {search_params['adults']}")
    else:
        print("👤 Mode: INTERACTIVE")
        search_params = get_user_input()
        if not search_params:
            return
    
    print("=" * 70)
    
    # Step 1: Load hotel keys from database
    print("\n[STEP 1] Loading hotel keys database...")
    hotel_keys = load_hotel_keys()
    
    if not hotel_keys:
        print("[ERROR] No hotel keys loaded. Exiting.")
        return
    
    # Step 2: Load Excel and process hotels
    print("\n[STEP 2] Loading Excel and fetching prices by key...")
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # Initialize counters
    hotels_total = 0
    hotels_with_key = 0
    hotels_with_prices = 0
    excel_hotels_with_prices = {}
    
    for row in range(2, ws.max_row + 1):
        hotel_name = ws.cell(row=row, column=1).value
        
        if not hotel_name:
            continue
        
        hotel_name = str(hotel_name).strip()
        hotels_total += 1
        
        hotel_key = hotel_keys.get(hotel_name)
        
        if hotel_key:
            hotels_with_key += 1
            print(f"\n[{hotels_with_key}] {hotel_name}")
            print(f"    Key: {hotel_key}")
            print(f"    Fetching price...")
            
            rate_data = get_hotel_rates(
                hotel_key, 
                search_params['chk_in'], 
                search_params['chk_out'],
                search_params['rooms'],
                search_params['adults']
            )
            
            if rate_data:
                price = rate_data['rate']
                provider = rate_data['provider']
                print(f"    Price: ${price:.2f} ({provider})")
                
                excel_hotels_with_prices[row] = {
                    'price': price,
                    'provider': provider,
                    'hotel_key': hotel_key
                }
                hotels_with_prices += 1
            else:
                print(f"    No price available")
                excel_hotels_with_prices[row] = {
                    'price': None,
                    'provider': 'N/A',
                    'hotel_key': hotel_key
                }
            
            time.sleep(REQUEST_DELAY)
        else:
            print(f"\n[SKIP] {hotel_name} - No key in database")
    
    print(f"\n[STATS] Hotels in Excel: {hotels_total}")
    print(f"[STATS] Hotels with keys: {hotels_with_key}")
    print(f"[STATS] Hotels with prices: {hotels_with_prices}")
    
    # Step 3: Update Excel
    if excel_hotels_with_prices:
        output_file = update_excel_with_prices(excel_hotels_with_prices, search_params, snapshot_date)
        print("\n" + "=" * 70)
        print("✅ [COMPLETE]")
        print(f"📁 Output: {output_file}")
        print(f"📊 {hotels_with_prices} hotels with prices")
        print(f"⏭️  {hotels_with_key - hotels_with_prices} hotels without prices")
        print(f"❌ {hotels_total - hotels_with_key} hotels without keys")
        print("=" * 70)
    else:
        print("\n[WARN] No hotels matched or priced")


if __name__ == "__main__":
    main()
