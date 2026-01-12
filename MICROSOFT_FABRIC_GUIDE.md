# Running Hotel API Scripts in Microsoft Fabric

Yes, you can run these scripts in **Microsoft Fabric** without any issues. Fabric provides an ideal environment for execution, automation, and integration with other data sources.

## Implementation Details

### 1. Execution Environment
The most efficient way to run these scripts is using **Fabric Notebooks**.
*   **Language:** Python (Standard or PySpark).
*   **Storage:** Excel files should be uploaded to a **Fabric Lakehouse** (inside the "Files" section).

## Migration Steps

### A. Prepare the Environment (Lakehouse)
1.  Create a **Lakehouse** in your Fabric Workspace.
2.  Upload your Excel files (e.g., `PRTC Endorsed Hotels (12.25).xlsx`) to the **Files** folder within the Lakehouse.

### B. Create the Notebook
1.  Create a new **Notebook** in Fabric.
2.  Attach it to the Lakehouse you created.
3.  Install dependencies in the first cell:
    ```python
    %pip install openpyxl requests
    ```

### C. Adjust File Paths
In your local scripts, paths are relative (e.g., `PRTC Endorsed Hotels (12.25).xlsx`). In Fabric, you must use Lakehouse paths:
*   **Local Path:** `EXCEL_FILE = "PRTC Endorsed Hotels (12.25).xlsx"`
*   **Fabric Path:** `EXCEL_FILE = "/lakehouse/default/Files/PRTC Endorsed Hotels (12.25).xlsx"`

### D. Handling .py Files
You have two main ways to use your existing `.py` scripts in Fabric:

#### Option 1: Upload to Lakehouse and Run (Recommended)
1.  In the Lakehouse explorer, right-click the **Files** folder -> **Upload** -> **Files**.
2.  Upload `hotel_price_updater.py`.
3.  In your Notebook, run it using the magic command:
    ```python
    %run /lakehouse/default/Files/hotel_price_updater.py
    ```

#### Option 2: Direct Spark Job
If you don't need the interactive notebook interface:
1.  Create a new **Spark Job Definition** in your workspace.
2.  Upload the `.py` file as the **Main definition file**.
3.  Upload your Excel files as **Reference files**.

### E. Secret Management (Recommended)
Instead of hardcoding the `RAPIDAPI_KEY`, use Fabric's security features or Workspace environment variables to store sensitive information.

## Advantages of Using Microsoft Fabric

1.  **Automation (Pipelines):** You can create a "Data Factory Pipeline" to run the script automatically on a schedule (e.g., weekly) to update prices without manual intervention.
2.  **Scalability:** If you need to process thousands of hotels, Fabric can scale easily using Spark.
3.  **Visualization:** Once the Excel is updated, you can convert the data into a **Lakehouse Table** and connect it directly to **Power BI** for real-time price monitoring dashboards.

## Environment-Aware Code Example

You can modify your scripts to automatically detect if they are running in Fabric:

```python
import os

# Detect if running in Fabric to adjust paths
is_fabric = os.path.exists('/lakehouse/default/Files/')
base_path = '/lakehouse/default/Files/' if is_fabric else './'

EXCEL_FILE = f"{base_path}PRTC Endorsed Hotels (12.25).xlsx"
OUTPUT_FILE = f"{base_path}PRTC Endorsed Hotels - Updated Prices.xlsx"
```
