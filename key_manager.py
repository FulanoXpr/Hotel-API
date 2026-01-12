from flask import Flask, render_template, request, jsonify
import openpyxl
import json
import os
import requests
import time

app = Flask(__name__)

# Configuration
EXCEL_FILE = "PRTC Endorsed Hotels (12.25).xlsx"
MAPPING_FILE = "hotel_mapping.json"
XOTELO_BASE_URL = "https://data.xotelo.com/api"

def load_mapping():
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_mapping(mapping):
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4, ensure_ascii=False)

def get_excel_hotels():
    if not os.path.exists(EXCEL_FILE):
        return []
    
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active
    hotels = []
    
    for row in range(2, ws.max_row + 1):
        name = ws.cell(row=row, column=1).value
        if name:
            hotels.append(name.strip())
    
    return sorted(list(set(hotels)))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/hotels')
def get_hotels():
    excel_hotels = get_excel_hotels()
    mapping = load_mapping()
    
    result = []
    for name in excel_hotels:
        result.append({
            'name': name,
            'key': mapping.get(name, ""),
            'status': 'mapped' if name in mapping else 'unmapped'
        })
    
    return jsonify(result)

@app.route('/api/search')
def search_api():
    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # Load cached hotels or fetch from API
        cache_file = "api_hotels_cache.json"
        all_hotels = []
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                all_hotels = json.load(f)
        else:
            # Fetch hotels from Xotelo /list endpoint (free, no auth needed)
            print("[CACHE] Fetching hotels from Xotelo list API...")
            for offset in range(0, 500, 100):
                response = requests.get(f"{XOTELO_BASE_URL}/list", params={
                    "location_key": "g147319",  # Puerto Rico
                    "limit": 100,
                    "offset": offset
                }, timeout=15)
                response.raise_for_status()
                data = response.json()
                hotels = data.get('result', {}).get('list', [])
                if not hotels:
                    break
                all_hotels.extend(hotels)
                time.sleep(0.5)
            
            # Cache results
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(all_hotels, f, ensure_ascii=False)
            print(f"[CACHE] Cached {len(all_hotels)} hotels")
        
        # Filter by query
        results = []
        for hotel in all_hotels:
            name = hotel.get('name', '').lower()
            if query in name:
                results.append({
                    'name': hotel.get('name'),
                    'hotel_key': hotel.get('key'),
                    'short_place_name': hotel.get('location', 'Puerto Rico')
                })
        
        # Sort by relevance (starts with query first)
        results.sort(key=lambda x: (0 if x['name'].lower().startswith(query) else 1, x['name']))
        
        return jsonify(results[:20])  # Limit to 20 results
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/map', methods=['POST'])
def map_hotel():
    data = request.json
    hotel_name = data.get('excel_name')
    hotel_key = data.get('api_key')
    
    if not hotel_name or not hotel_key:
        return jsonify({"error": "Missing data"}), 400
    
    mapping = load_mapping()
    mapping[hotel_name] = hotel_key
    save_mapping(mapping)
    
    return jsonify({"success": True})

@app.route('/api/unmap', methods=['POST'])
def unmap_hotel():
    data = request.json
    hotel_name = data.get('excel_name')
    
    mapping = load_mapping()
    if hotel_name in mapping:
        del mapping[hotel_name]
        save_mapping(mapping)
    
    return jsonify({"success": True})

if __name__ == '__main__':
    print("Starting Hotel Key Manager on http://localhost:5000")
    app.run(debug=True, port=5000)
