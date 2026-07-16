"""
fetch_price_history.py
--------------------------------
Fetches daily price history (Open/High/Low/Close/Volume) for every
Mainboard IPO company, from its listing date up to today, using yfinance.

Input:  ../_datasets/_raw/ipo_performance_raw.csv
        (must contain: ipo_company_name, ipo_issue_type, il_ipo_listing_date,
         il_nse_script_symbol)

Output: ../_datasets/_raw/price_history_raw.csv
        Long format: one row per company per trading day.

Run this script from inside the _scripts/ folder:
    python fetch_price_history.py
"""

import pandas as pd
import yfinance as yf
import time
import os

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
INPUT_PATH = os.path.join("..", "_datasets", "_raw", "ipo_performance_raw.csv")
OUTPUT_PATH = os.path.join("..", "_datasets", "_raw", "price_history_raw.csv")
SKIPPED_LOG_PATH = os.path.join("..", "_datasets", "_raw", "price_history_skipped.csv")

END_DATE = None  # None = fetch up to today. Set to "2026-07-15" style string to override.
SLEEP_BETWEEN_CALLS = 1.5  # seconds, be polite to Yahoo Finance


def load_ticker_list() -> pd.DataFrame:
    """Load the IPO master file and build a clean ticker list."""
    df = pd.read_csv(INPUT_PATH)

    # Only keep actual IPOs (drop REIT / FPO / InvIT / SM REIT)
    df = df[df["ipo_issue_type"] == "IPO"].copy()

    # Drop rows with no NSE ticker -- yfinance is unreliable for BSE-only symbols
    before = len(df)
    df = df.dropna(subset=["il_nse_script_symbol"]).copy()
    dropped = before - len(df)
    if dropped:
        print(f"Skipping {dropped} companies with no NSE ticker symbol.")

    # Clean listing date to a plain date string
    df["listing_date_clean"] = pd.to_datetime(df["il_ipo_listing_date"]).dt.strftime("%Y-%m-%d")

    # Build the Yahoo Finance ticker (NSE tickers need a .NS suffix)
    df["yf_ticker"] = df["il_nse_script_symbol"].str.strip() + ".NS"

    return df[["ipo_company_name", "yf_ticker", "listing_date_clean"]].reset_index(drop=True)


def fetch_price_history(ticker: str, start_date: str, company_name: str) -> pd.DataFrame:
    """Fetch daily OHLCV for one ticker from start_date to END_DATE (or today)."""
    data = yf.download(
        ticker,
        start=start_date,
        end=END_DATE,
        progress=False,
        auto_adjust=False,
    )

    if data.empty:
        return pd.DataFrame()

    # yfinance sometimes returns MultiIndex columns when downloading a single
    # ticker depending on version -- flatten just in case
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    data["Company"] = company_name
    data["Ticker"] = ticker

    return data[["Company", "Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]]


def main():
    tickers_df = load_ticker_list()
    print(f"Fetching price history for {len(tickers_df)} companies...\n")

    all_price_data = []
    skipped = []

    for i, row in tickers_df.iterrows():
        company = row["ipo_company_name"]
        ticker = row["yf_ticker"]
        start_date = row["listing_date_clean"]

        print(f"[{i+1}/{len(tickers_df)}] {company} ({ticker}) from {start_date}...")

        try:
            df = fetch_price_history(ticker, start_date, company)
            if df.empty:
                print(f"  WARNING: No price data returned for {ticker}.")
                skipped.append({"Company": company, "Ticker": ticker, "Reason": "empty_result"})
            else:
                all_price_data.append(df)
                print(f"  -> {len(df)} trading days fetched.")
        except Exception as e:
            print(f"  ERROR fetching {ticker}: {e}")
            skipped.append({"Company": company, "Ticker": ticker, "Reason": str(e)})

        time.sleep(SLEEP_BETWEEN_CALLS)

    if not all_price_data:
        print("\nNo price data collected at all. Exiting without writing a file.")
        return

    combined = pd.concat(all_price_data, ignore_index=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(combined)} total rows ({combined['Company'].nunique()} companies) to {OUTPUT_PATH}")

    if skipped:
        skipped_df = pd.DataFrame(skipped)
        skipped_df.to_csv(SKIPPED_LOG_PATH, index=False)
        print(f"Logged {len(skipped_df)} skipped/failed companies to {SKIPPED_LOG_PATH}")


if __name__ == "__main__":
    main()