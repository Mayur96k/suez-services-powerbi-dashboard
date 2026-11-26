"""
Clean the raw scraped data and produce the analysis-ready dataset
used by the analysis script and the Power BI dashboard.

Input:  01_Webscraping/suez_services_raw.csv
Output: 03_Data/suez_services_clean.csv

Usage:
    python 02_ETL/etl_transform.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "01_Webscraping" / "suez_services_raw.csv"
CLEAN_FILE = ROOT / "03_Data" / "suez_services_clean.csv"

# Approximate bounding boxes, good enough to tell the two countries apart
NZ_BOUNDS = {"lat": (-47.5, -34.0), "lon": (165.0, 179.9)}
AU_BOUNDS = {"lat": (-44.0, -9.0), "lon": (112.0, 154.0)}

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("etl")


def extract(path: Path = RAW_FILE) -> pd.DataFrame:
    return pd.read_csv(path)


def _country(lat: float, lon: float) -> str:
    if NZ_BOUNDS["lat"][0] <= lat <= NZ_BOUNDS["lat"][1] and NZ_BOUNDS["lon"][0] <= lon <= NZ_BOUNDS["lon"][1]:
        return "New Zealand"
    if AU_BOUNDS["lat"][0] <= lat <= AU_BOUNDS["lat"][1] and AU_BOUNDS["lon"][0] <= lon <= AU_BOUNDS["lon"][1]:
        return "Australia"
    return "Unknown"


def transform(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Tidy text columns
    for col in ("service_name", "service_type"):
        out[col] = out[col].astype("string").str.strip()
    out["service_type"] = out["service_type"].fillna("Unknown")

    # Coordinates must be numeric and present
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce").round(6)
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce").round(6)
    missing = out[["latitude", "longitude"]].isna().any(axis=1)
    if missing.any():
        log.warning("Dropping %d rows without valid coordinates", int(missing.sum()))
    out = out[~missing]

    # Remove exact duplicates and duplicate sites (same name and coordinates)
    before = len(out)
    out = out.drop_duplicates(subset=["service_name", "latitude", "longitude"])
    log.info("Removed %d duplicate rows", before - len(out))

    # Enrich
    out["country"] = [_country(la, lo) for la, lo in zip(out["latitude"], out["longitude"])]
    out["last_updated_at_UTC"] = pd.to_datetime(out["last_updated_at_UTC"], format="%d-%b-%Y %H:%M:%S")

    columns = ["service_name", "service_type", "country", "latitude", "longitude",
               "service_icon", "last_updated_at_UTC"]
    return out[columns].sort_values(["country", "service_type", "service_name"]).reset_index(drop=True)


def validate(df: pd.DataFrame) -> None:
    assert df["service_name"].notna().all(), "service_name has empty values"
    assert df["latitude"].between(-90, 90).all() and df["longitude"].between(-180, 180).all(), "invalid coordinates"
    assert not df.duplicated(["service_name", "latitude", "longitude"]).any(), "duplicates remain"


def load(df: pd.DataFrame, path: Path = CLEAN_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


def main() -> None:
    raw = extract()
    log.info("Read %d raw rows", len(raw))
    clean = transform(raw)
    validate(clean)
    load(clean)
    log.info("Wrote %d clean rows to %s", len(clean), CLEAN_FILE.relative_to(ROOT))
    log.info("By country: %s", clean["country"].value_counts().to_dict())


if __name__ == "__main__":
    main()
