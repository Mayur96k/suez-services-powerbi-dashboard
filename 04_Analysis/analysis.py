"""
Exploratory analysis of SUEZ ANZ service locations.

Reads the clean dataset, prints key figures and saves:
  docs/images/service_types.png      - number of sites per service type
  docs/images/site_locations.png     - site coordinates coloured by service type
  04_Analysis/outputs/summary.csv    - counts by service type and country
  04_Analysis/outputs/service_map.html  - interactive map (if folium is installed)

Usage:
    python 04_Analysis/analysis.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLEAN_FILE = ROOT / "03_Data" / "suez_services_clean.csv"
IMAGES = ROOT / "docs" / "images"
OUTPUTS = Path(__file__).resolve().parent / "outputs"

# Colour-blind-safe categorical palette, assigned in a fixed order
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

plt.rcParams.update({
    "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "axes.edgecolor": GRID,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def load() -> pd.DataFrame:
    return pd.read_csv(CLEAN_FILE)


def summary(df: pd.DataFrame) -> pd.DataFrame:
    table = pd.crosstab(df["service_type"], df["country"], margins=True, margins_name="Total")
    return table.sort_values("Total", ascending=False)


def chart_service_types(df: pd.DataFrame, path: Path) -> None:
    counts = df["service_type"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    ax.barh(counts.index, counts.values, color=PALETTE[0], height=0.6)
    total = counts.sum()
    for y, (name, value) in enumerate(counts.items()):
        ax.text(value + 0.6, y, f"{value}  ({value / total:.0%})", va="center", fontsize=9, color=INK)
    ax.set_title("SUEZ ANZ service locations by type", pad=24)
    ax.text(0, 1.015, f"{total} sites · snapshot {df['last_updated_at_UTC'].iloc[0][:10]}",
            transform=ax.transAxes, color=MUTED, fontsize=9, va="bottom")
    ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.spines["left"].set_visible(False)
    ax.tick_params(length=0)
    ax.set_xlim(0, counts.max() * 1.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_locations(df: pd.DataFrame, path: Path) -> None:
    order = df["service_type"].value_counts().index.tolist()
    colour = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(order)}
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=150)
    for t in order:
        part = df[df["service_type"] == t]
        ax.scatter(part["longitude"], part["latitude"], s=36, color=colour[t], label=f"{t} ({len(part)})",
                   edgecolor=SURFACE, linewidth=0.8, zorder=3)
    ax.set_title("Where the sites are", pad=24)
    ax.text(0, 1.015, "Latitude / longitude of each site · Australia and New Zealand",
            transform=ax.transAxes, color=MUTED, fontsize=9, va="bottom")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.grid(color=GRID, linewidth=0.6, zorder=0)
    ax.set_aspect("equal", adjustable="datalim")
    ax.legend(loc="lower left", frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def interactive_map(df: pd.DataFrame, path: Path) -> bool:
    try:
        import folium
    except ImportError:
        return False
    m = folium.Map(location=[-30, 145], zoom_start=4)  # OpenStreetMap tiles, no API key needed
    order = df["service_type"].value_counts().index.tolist()
    colour = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(order)}
    for row in df.itertuples():
        folium.CircleMarker(
            location=[row.latitude, row.longitude], radius=6, color=colour[row.service_type],
            fill=True, fill_opacity=0.85, popup=f"<b>{row.service_name}</b><br>{row.service_type}",
        ).add_to(m)
    m.save(str(path))
    return True


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    df = load()

    table = summary(df)
    table.to_csv(OUTPUTS / "summary.csv")
    print(f"Sites: {len(df)}  |  Service types: {df['service_type'].nunique()}  |  "
          f"Countries: {df['country'].value_counts().to_dict()}")
    print(table.to_string())

    chart_service_types(df, IMAGES / "service_types.png")
    chart_locations(df, IMAGES / "site_locations.png")
    if interactive_map(df, OUTPUTS / "service_map.html"):
        print("Interactive map saved to 04_Analysis/outputs/service_map.html")
    else:
        print("folium not installed: skipped the interactive map (pip install folium)")


if __name__ == "__main__":
    main()
