# Hotel Price Updater API

Automated system for fetching and updating hotel prices in Puerto Rico using the **Xotelo API** (TripAdvisor-based). This project matches local hotel names from PRTC endorsed lists with real-time market data.

## 📋 Project Overview

The system processes Excel files containing lists of endorsed hotels, searches for their equivalents on TripAdvisor/Xotelo, and retrieves the lowest available price for a specific date range.

### Key Features
*   **Mass Matching:** Fuzzy string matching to link local names with API entities.
*   **Price Extraction:** Retrieves the lowest nightly rate from multiple providers.
*   **Excel Integration:** Updates original spreadsheets with price, provider, and match quality scores.
*   **Fabric Ready:** Optimized for cloud execution in Microsoft Fabric.

## 🚀 Main Scripts

1.  **`xotelo_price_updater.py`**: The primary engine. It performs bulk collection of hotels in Puerto Rico and matches them against the Excel list.
2.  **`xotelo_price_fixer.py`**: A specialized utility to perform deep searches and price retries for hotels that were not matched in the initial automation pass.

## 🛠️ Installation & Setup

1.  Ensure you have Python 3.8+ installed.
2.  Install dependencies:
    ```bash
    pip install requests openpyxl
    ```
3.  Place your source file `PRTC Endorsed Hotels (12.25).xlsx` in the root directory.

## ☁️ Microsoft Fabric Deployment

This project is fully compatible with Microsoft Fabric. For detailed instructions on how to set up Lakehouses, Notebooks, and automated Pipelines, please refer to:

👉 **[Microsoft Fabric Migration Guide](MICROSOFT_FABRIC_GUIDE.md)**

## 📊 Data Mapping
The system adds the following columns to the output Excel:
*   `Xotelo_Price_USD`: The lowest retrieved nightly rate.
*   `Provider`: The booking site offering the rate.
*   `API_Match_Name`: The hotel name as found in the API.
*   `Match_Score`: Confidence level of the name matching.