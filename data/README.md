# Fund Data

Place your 10 FSMOne fund price CSVs in this folder, or upload them directly via the app sidebar.

## How to download from FSMOne

1. Go to https://secure.fundsupermart.com/fsm/funds/fund-selector
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
