"""
Scrape SUEZ Australia & New Zealand service locations.

Calls the public JSON endpoint behind the location map on suez.com.au and
saves one row per service location, joined to its service type.

Output: 01_Webscraping/suez_services_raw.csv

Usage:
    python 01_Webscraping/scrape_suez_services.py
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

MAP_URL = (
    "https://www.suez.com.au/en-AU/api/LocationMap/InitMap"
    "?idMap={629C6BF1-8BD9-456D-BF49-9B1E24AFC1B6}"
)
OUTPUT_FILE = Path(__file__).resolve().parent / "suez_services_raw.csv"
TIMEOUT_SECONDS = 30

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("scraper")


def fetch_map_data(url: str = MAP_URL) -> dict:
    """Download the location-map JSON (TLS certificate verification stays on)."""
    response = requests.get(url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": "suez-services-dashboard/1.0"})
    response.raise_for_status()
    return response.json()


def extract_service_locations(payload: dict) -> pd.DataFrame:
    """One row per point of interest: name, coordinates and the icon that identifies its type."""
    rows = [
        {
            "icon_id": poi["IconId"].strip("{}"),
            "service_name": poi["Name"],
            "latitude": poi["Lat"],
            "longitude": poi["Lng"],
        }
        for poi in payload.get("PoiItem", [])
    ]
    return pd.DataFrame(rows)


def extract_service_types(payload: dict) -> pd.DataFrame:
    """One row per map icon: its legend (service type) and image URL."""
    rows = [
        {
            "icon_id": icon["Id"].strip("{}"),
            "service_type": icon["Legend"],
            "service_icon": icon["Image"],
        }
        for icon in payload.get("MapIcon", [])
    ]
    return pd.DataFrame(rows)


def build_dataset(locations: pd.DataFrame, types: pd.DataFrame) -> pd.DataFrame:
    """Join locations to their service type and stamp the extraction time (UTC)."""
    services = locations.merge(types, on="icon_id", how="left").drop(columns="icon_id")
    services["last_updated_at_UTC"] = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M:%S")
    return services


def main() -> None:
    start = time.perf_counter()
    log.info("Downloading SUEZ location map data...")
    payload = fetch_map_data()

    locations = extract_service_locations(payload)
    types = extract_service_types(payload)
    log.info("Found %d service locations and %d service types", len(locations), len(types))

    services = build_dataset(locations, types)
    services.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    log.info("Saved %d rows to %s in %.1f s", len(services), OUTPUT_FILE.name, time.perf_counter() - start)


if __name__ == "__main__":
    main()
