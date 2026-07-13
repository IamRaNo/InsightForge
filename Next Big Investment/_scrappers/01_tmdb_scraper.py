"""
01_tmdb_scraper.py

Purpose:
    First stage of the "Next Big Investment" data pipeline.
    Collects metadata for all Hindi-language movies released between
    2020-01-01 and 2026-12-31 using the TMDB API (Discover + Movie Details).

Output:
    _raw_data/tmdb_movies_raw.csv
    _raw_data/failed_tmdb_ids.csv (only if failures occur)

Usage:
    Place a .env file next to this script with:
        TMDB_BEARER_TOKEN=your_token_here
    Then run:
        python 01_tmdb_scraper.py
"""

import os
import time
import logging
from typing import Any, Optional

import requests
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TMDB_BASE_URL = "https://api.themoviedb.org/3"
DISCOVER_ENDPOINT = f"{TMDB_BASE_URL}/discover/movie"
MOVIE_DETAILS_ENDPOINT = f"{TMDB_BASE_URL}/movie/{{movie_id}}"

RAW_DATA_DIR = "_raw_data"
OUTPUT_CSV = os.path.join(RAW_DATA_DIR, "tmdb_movies_raw.csv")
FAILED_IDS_CSV = os.path.join(RAW_DATA_DIR, "failed_tmdb_ids.csv")

ORIGINAL_LANGUAGE = "hi"          # Hindi
RELEASE_DATE_FROM = "2020-01-01"
RELEASE_DATE_TO = "2026-12-31"

MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2          # exponential backoff: 2, 4, 8...
REQUEST_TIMEOUT = 15

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__) or ".", "tmdb_scraper.log"))
    ]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

def load_bearer_token() -> str:
    """Load the TMDB bearer token from the .env file."""
    load_dotenv()
    token = os.getenv("TMDB_BEARER_TOKEN")
    if not token:
        raise EnvironmentError(
            "TMDB_BEARER_TOKEN not found. Please set it in a .env file."
        )
    return token


def ensure_output_dir(path: str) -> None:
    """Create the raw data directory if it doesn't already exist."""
    os.makedirs(path, exist_ok=True)


def get_headers(token: str) -> dict:
    """Build request headers with the bearer token."""
    return {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }


# ---------------------------------------------------------------------------
# Core request handler with retry + exponential backoff
# ---------------------------------------------------------------------------

def make_request(url: str, headers: dict, params: Optional[dict] = None) -> Optional[dict]:
    """
    Make a GET request with retry and exponential backoff.
    Returns the parsed JSON response, or None if all retries fail.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()

            # Handle rate limiting explicitly
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", BACKOFF_BASE_SECONDS))
                logger.warning(f"Rate limited. Waiting {retry_after}s before retry...")
                time.sleep(retry_after)
                continue

            logger.warning(
                f"Request failed (status {response.status_code}) on attempt {attempt}/{MAX_RETRIES}: {url}"
            )

        except requests.RequestException as e:
            logger.warning(f"Request exception on attempt {attempt}/{MAX_RETRIES}: {e}")

        if attempt < MAX_RETRIES:
            wait_time = BACKOFF_BASE_SECONDS ** attempt
            time.sleep(wait_time)

    logger.error(f"All {MAX_RETRIES} attempts failed for: {url}")
    return None


# ---------------------------------------------------------------------------
# Discovery: get all Hindi movie IDs in the date range
# ---------------------------------------------------------------------------

def discover_hindi_movies(headers: dict) -> list[dict]:
    """
    Iterate through TMDB's discover endpoint to collect all Hindi-language
    movies released within the target date range.
    Returns a list of minimal movie dicts (id, title, etc. from discover results).
    """
    logger.info("Starting movie discovery phase...")

    base_params = {
        "with_original_language": ORIGINAL_LANGUAGE,
        "primary_release_date.gte": RELEASE_DATE_FROM,
        "primary_release_date.lte": RELEASE_DATE_TO,
        "sort_by": "primary_release_date.asc",
        "page": 1,
    }

    # First request to determine total number of pages
    first_page = make_request(DISCOVER_ENDPOINT, headers, params=base_params)
    if not first_page:
        logger.error("Failed to fetch the first discover page. Aborting discovery.")
        return []

    total_pages = first_page.get("total_pages", 1)
    total_results = first_page.get("total_results", 0)
    logger.info(f"Discovered {total_results} movies across {total_pages} pages.")

    all_movies: list[dict] = first_page.get("results", [])

    # TMDB caps discover results at 500 pages
    total_pages = min(total_pages, 500)

    for page in tqdm(range(2, total_pages + 1), desc="Collecting pages"):
        logger.info(f"Processing discover page {page}/{total_pages}")
        params = dict(base_params)
        params["page"] = page

        page_data = make_request(DISCOVER_ENDPOINT, headers, params=params)
        if page_data and "results" in page_data:
            all_movies.extend(page_data["results"])
        else:
            logger.warning(f"Skipping page {page} due to repeated failures.")

    logger.info(f"Total movies collected from discovery: {len(all_movies)}")
    return all_movies


# ---------------------------------------------------------------------------
# Movie details fetch + field extraction
# ---------------------------------------------------------------------------

def join_field(items: Optional[list[dict]], key: str) -> str:
    """Convert a list of dicts (e.g. genres) into a comma-separated string."""
    if not items:
        return ""
    return ", ".join(str(item.get(key, "")) for item in items if item.get(key))


def extract_movie_fields(details: dict) -> dict:
    """Extract only the required fields from a TMDB movie details response."""
    release_date = details.get("release_date") or ""
    release_year = release_date.split("-")[0] if release_date else ""

    collection = details.get("belongs_to_collection")
    collection_name = collection.get("name") if collection else ""

    return {
        "tmdb_id": details.get("id"),
        "imdb_id": details.get("imdb_id"),
        "title": details.get("title"),
        "original_title": details.get("original_title"),
        "original_language": details.get("original_language"),
        "overview": details.get("overview"),
        "tagline": details.get("tagline"),
        "status": details.get("status"),
        "adult": details.get("adult"),
        "release_date": release_date,
        "release_year": release_year,
        "runtime": details.get("runtime"),
        "vote_average": details.get("vote_average"),
        "vote_count": details.get("vote_count"),
        "popularity": details.get("popularity"),
        "budget": details.get("budget"),
        "revenue": details.get("revenue"),
        "genres": join_field(details.get("genres"), "name"),
        "production_companies": join_field(details.get("production_companies"), "name"),
        "production_countries": join_field(details.get("production_countries"), "name"),
        "spoken_languages": join_field(details.get("spoken_languages"), "english_name"),
        "homepage": details.get("homepage"),
        "belongs_to_collection": collection_name,
    }


def fetch_all_movie_details(movie_ids: list[int], headers: dict) -> tuple[list[dict], list[int]]:
    """
    Fetch full details for each discovered movie ID.
    Returns (list_of_extracted_records, list_of_failed_ids).
    """
    logger.info("Starting movie details collection phase...")

    records: list[dict] = []
    failed_ids: list[int] = []

    for movie_id in tqdm(movie_ids, desc="Fetching movie details"):
        url = MOVIE_DETAILS_ENDPOINT.format(movie_id=movie_id)
        details = make_request(url, headers)

        if details:
            records.append(extract_movie_fields(details))
        else:
            logger.error(f"Failed to fetch details for TMDB ID: {movie_id}")
            failed_ids.append(movie_id)

    logger.info(f"Successfully collected details for {len(records)} movies.")
    logger.info(f"Failed to collect details for {len(failed_ids)} movies.")

    return records, failed_ids


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def save_records_to_csv(records: list[dict], output_path: str) -> None:
    """Save extracted movie records into the raw CSV output."""
    if not records:
        logger.warning("No records to save. CSV will not be created.")
        return

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved {len(df)} records to {output_path}")


def save_failed_ids(failed_ids: list[int], output_path: str) -> None:
    """Save failed TMDB IDs to a separate CSV for later retry/inspection."""
    if not failed_ids:
        logger.info("No failed IDs to save.")
        return

    df = pd.DataFrame({"tmdb_id": failed_ids})
    df.to_csv(output_path, index=False)
    logger.warning(f"Saved {len(failed_ids)} failed IDs to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=" * 60)
    logger.info("TMDB Scraper started (Next Big Investment pipeline - Stage 1)")
    logger.info("=" * 60)

    ensure_output_dir(RAW_DATA_DIR)
    token = load_bearer_token()
    headers = get_headers(token)

    # Step 1: Discover all Hindi movies in the date range
    discovered_movies = discover_hindi_movies(headers)
    if not discovered_movies:
        logger.error("No movies discovered. Exiting.")
        return

    movie_ids = [m["id"] for m in discovered_movies if m.get("id")]
    logger.info(f"Total unique movie IDs to process: {len(set(movie_ids))}")

    # Step 2: Fetch full details for each movie
    records, failed_ids = fetch_all_movie_details(list(dict.fromkeys(movie_ids)), headers)

    # Step 3: Save outputs
    save_records_to_csv(records, OUTPUT_CSV)
    save_failed_ids(failed_ids, FAILED_IDS_CSV)

    # Final summary
    logger.info("=" * 60)
    logger.info("Execution Summary")
    logger.info(f"Movies discovered : {len(movie_ids)}")
    logger.info(f"Movies collected  : {len(records)}")
    logger.info(f"Movies failed     : {len(failed_ids)}")
    logger.info(f"Output file       : {OUTPUT_CSV}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()