# Fund Data

Place your 10 FSMOne fund price CSVs in this folder, or upload them directly via the app sidebar.

## Download from FSMOne

Use the downloader script to fetch app-compatible CSVs into this folder:

```bash
python scripts/download_fsmone_funds.py
```

By default, it downloads the project basket for `2021-01-01` through `2025-12-31`.
You can pass FSMOne fund codes or quoted product names:

```bash
python scripts/download_fsmone_funds.py FI3095 JPM048 --start-date 2021-01-01 --end-date 2025-12-31
python scripts/download_fsmone_funds.py --identifier "Fidelity America A-SGD (hedged)"
```

Generated CSVs are ignored by Git via `data/*.csv`.

## How to download from FSMOne

1. Go to https://secure.fundsupermart.com/fsmone/tools/fund-selector
2. Search for and open any fund
3. Navigate to the **Price History** tab
4. Set your desired date range (recommend 5+ years for a meaningful efficient frontier)
5. Download as CSV
6. Rename the file to the fund's short name (e.g. `LionGlobal_Growth.csv`)
7. Repeat for 10 different funds across different asset classes / geographies

## Expected CSV format

The loader auto-detects the data rows, so any format where:
- Column 1 is a date (DD/MM/YYYY or YYYY-MM-DD)
- Column 2 is a price (numeric, commas allowed)

...will work. Metadata header rows at the top are automatically skipped.
