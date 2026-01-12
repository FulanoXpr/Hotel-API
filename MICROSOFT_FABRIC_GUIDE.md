# Running Hotel API Scripts in Microsoft Fabric

This guide explains how to deploy the Hotel Price Updater in **Microsoft Fabric** for cloud execution and monthly automation.

## Quick Start

### Required Files for Fabric
Upload these to your Lakehouse `Files` folder:
- `xotelo_price_updater.py` - Main script
- `hotel_keys_db.json` - Hotel key mappings (149 hotels)
- `PRTC Endorsed Hotels (12.25).xlsx` - Source data

## Implementation Steps

### 1. Create Lakehouse
1. Create a **Lakehouse** in your Fabric Workspace
2. Upload all required files to the **Files** folder

### 2. Create Notebook
1. Create a new **Notebook** in Fabric
2. Attach it to your Lakehouse
3. Install dependencies:
   ```python
   %pip install openpyxl requests
   ```

### 3. Modify Script Paths
The script needs Fabric-compatible paths. Add this code at the top:

```python
import os

# Auto-detect Fabric environment
is_fabric = os.path.exists('/lakehouse/default/Files/')
base_path = '/lakehouse/default/Files/' if is_fabric else './'

EXCEL_FILE = f"{base_path}PRTC Endorsed Hotels (12.25).xlsx"
HOTEL_KEYS_DB = f"{base_path}hotel_keys_db.json"
# Output will include date: PRTC_Hotels_Prices_2026-01-12.xlsx
```

### 4. Run in Automatic Mode
In your Fabric Notebook, execute the script with `--auto` flag:

```python
import sys
sys.argv = ['xotelo_price_updater.py', '--auto']
%run /lakehouse/default/Files/xotelo_price_updater.py
```

Or import and run directly:
```python
# Set auto mode
import sys
sys.argv = ['script', '--auto']

# Run the updater
exec(open('/lakehouse/default/Files/xotelo_price_updater.py').read())
```

## Monthly Automation with Pipelines

### Option 1: Data Factory Pipeline
1. Go to your Workspace → **New** → **Data Pipeline**
2. Add a **Notebook** activity
3. Select your price updater notebook
4. Set **Schedule trigger**: Monthly (e.g., 1st of each month)

### Option 2: Spark Job Definition
1. Create **Spark Job Definition** in workspace
2. Upload `xotelo_price_updater.py` as main file
3. Set arguments: `--auto`
4. Schedule monthly execution

## Output Files

Each run creates a dated output file:
```
PRTC_Hotels_Prices_2026-01-12.xlsx
PRTC_Hotels_Prices_2026-02-01.xlsx
...
```

These accumulate in your Lakehouse for historical analysis.

## Power BI Integration

To create price monitoring dashboards:

1. Convert Excel outputs to **Lakehouse Table**:
   ```python
   import pandas as pd
   from datetime import datetime
   
   # Read latest prices
   df = pd.read_excel(f'{base_path}PRTC_Hotels_Prices_{datetime.now().strftime("%Y-%m-%d")}.xlsx')
   
   # Write to Lakehouse table
   spark_df = spark.createDataFrame(df)
   spark_df.write.mode('append').saveAsTable('hotel_prices_history')
   ```

2. Connect Power BI to the `hotel_prices_history` table

3. Build dashboards showing:
   - Price trends over time
   - Provider comparison
   - Regional pricing analysis

## Advantages of Fabric Deployment

| Feature | Benefit |
|---------|---------|
| **Scheduled Pipelines** | Automatic monthly price collection |
| **Lakehouse Storage** | Historical data preservation |
| **Power BI Integration** | Real-time dashboards |
| **Scalability** | Handle larger hotel lists easily |
| **No Local Machine** | Runs in cloud, no manual intervention |

## Troubleshooting

### Common Issues

**File not found errors:**
- Ensure all files are in `/lakehouse/default/Files/`
- Check file names match exactly (case-sensitive)

**Module not found:**
- Run `%pip install openpyxl requests` in first notebook cell

**API timeout:**
- Fabric may need longer timeouts; increase `TIMEOUT = 60` in script
