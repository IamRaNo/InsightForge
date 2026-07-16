"""
fetch_ipo_performance.py
--------------------------------
Fetches Mainboard IPO data from Chittorgarh's year-wise IPO Performance
Tracker pages.

IMPORTANT: This page renders its table via embedded JavaScript (Next.js),
not a plain HTML <table>. So instead of pandas.read_html(), we extract the
JSON data object embedded directly in the page source using a regex, then
parse it with json.loads(). This actually gives us MORE fields than a
simple HTML table would -- including subscription ratios (QIB/NII/RII),
issue size, and issue type -- not just Day 1 gain / Current gain.

Source: https://www.chittorgarh.com/ipo/ipo_perf_tracker.asp?year=<YEAR>

Output: saves one combined CSV to ../_datasets/_raw/ipo_performance_raw.csv

Run this script from inside the _scripts/ folder:
    python fetch_ipo_performance.py
"""

import pandas as pd
import requests
import re
import json
import time
import os

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]  # adjust range as needed
BASE_URL = "https://www.chittorgarh.com/ipo/ipo_perf_tracker.asp?year={year}"
OUTPUT_PATH = os.path.join("..", "_datasets", "_raw", "ipo_performance_raw.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Regex to find each company's JSON record embedded in the page's script tags.
# Records look like: {\"ipo_id\":2117,\"ipo_company_name\":\"...\", ... ,\"last_modified_date\":\"2026-07-14\"}
RECORD_PATTERN = re.compile(r'\{\\"ipo_id\\":\d+.*?\\"last_modified_date\\":\\"[\d-]*\\"\}')

# Columns we actually care about keeping (the raw records have some noisy/
# duplicate internal fields we don't need for analysis)
KEEP_COLUMNS = [
    "ipo_company_name",       # Company Name
    "ipo_issue_type",          # IPO / REIT / InvIT / SM REIT -- filter to "IPO" later
    "ipo_issue_price_final",   # Issue Price
    "il_ipo_listing_date",     # Listing Date
    "il_bse_script_code",      # BSE code
    "il_nse_script_symbol",    # NSE ticker symbol
    "ipo_issue_size_in_amt",   # Issue size (in amount, not Cr -- convert later)
    "change_in_percentage_listing_day",  # Day 1 Gain %
    "ipo_profit_loss",         # Current Gain % (as of last_modified_date)
    "ildt_open_price",         # Day 1 open
    "ildt_close_price",        # Day 1 close
    "ildt_high_price",         # Day 1 high
    "ildt_low_price",          # Day 1 low
    "qib",                     # Qualified Institutional Buyers subscription (x times)
    "nii",                     # Non-Institutional Investors subscription (x times)
    "rii",                     # Retail Individual Investors subscription (x times)
    "emp",                     # Employee subscription (x times)
    "total",                   # Overall subscription (x times)
    "last_modified_date",      # Date this "current" snapshot reflects
]


def fetch_year(year: int) -> pd.DataFrame:
    """Fetch and extract all IPO records for a single year."""
    url = BASE_URL.format(year=year)
    print(f"Fetching {year} -> {url}")

    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    matches = RECORD_PATTERN.findall(response.text)

    records = []
    for m in matches:
        unescaped = m.replace('\\"', '"')
        try:
            obj = json.loads(unescaped)
            records.append(obj)
        except json.JSONDecodeError:
            continue  # skip malformed fragments, don't crash the whole run

    if not records:
        print(f"  WARNING: No records extracted for {year}. Page structure may have changed.")
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Keep only columns we care about (some years/records may be missing a
    # few fields -- reindex fills those with NaN instead of erroring out)
    df = df.reindex(columns=KEEP_COLUMNS)

    df["Year"] = year
    print(f"  -> {len(df)} companies found for {year}")
    return df


def main():
    all_years_data = []

    for year in YEARS:
        try:
            df = fetch_year(year)
            if not df.empty:
                all_years_data.append(df)
        except Exception as e:
            print(f"  ERROR fetching {year}: {e}")

        time.sleep(2)  # polite delay between requests

    if not all_years_data:
        print("No data collected. Exiting without writing a file.")
        return

    combined = pd.concat(all_years_data, ignore_index=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(combined)} total rows to {OUTPUT_PATH}")
    print(f"IPO issue types found: {combined['ipo_issue_type'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()