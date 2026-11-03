"""
fetch_aqi_standalone.py — one-time AQI fetch. Run this BEFORE starting the app.

It reads the training cache, then fills any missing states by hitting Open-Meteo
sequentially (1 request at a time, no parallelization = no rate limits).
Saves the result to artifacts/aqi_5yr_cache.json — the app reads only from
this file, never the network.

Run:  python fetch_aqi_standalone.py
"""
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# ── config ──
CACHE_JSON = Path("artifacts/aqi_5yr_cache.json")
TRAINING_CSV = Path("xgb/data/aqi_cache.csv")
YEARS = 5
DELAY_BETWEEN_REQUESTS = 1.0  # avoid rate limits

# ── state name lookup ──
STATE_NAMES = {
    1: "Alabama", 2: "Alaska", 4: "Arizona", 5: "Arkansas", 6: "California",
    8: "Colorado", 9: "Connecticut", 10: "Delaware", 11: "Florida",
    12: "Georgia", 15: "Hawaii", 16: "Idaho", 17: "Illinois", 18: "Indiana",
    19: "Iowa", 20: "Kansas", 21: "Kentucky", 22: "Louisiana", 23: "Maine",
    24: "Maryland", 25: "Massachusetts", 26: "Michigan", 27: "Minnesota",
    28: "Mississippi", 29: "Missouri", 30: "Montana", 31: "Nebraska",
    32: "Nevada", 33: "New Hampshire", 34: "New Jersey", 35: "New Mexico",
    36: "New York", 37: "North Carolina", 38: "North Dakota", 39: "Ohio",
    40: "Oklahoma", 41: "Oregon", 42: "Pennsylvania", 44: "Rhode Island",
    45: "South Carolina", 46: "South Dakota", 47: "Tennessee", 48: "Texas",
    49: "Utah", 50: "Vermont", 51: "Virginia", 53: "Washington",
    54: "West Virginia", 55: "Wisconsin", 56: "Wyoming",
}

# ── coordinates ──
COORDS = {
    "Alabama": (32.806671, -86.791130), "Alaska": (61.370716, -152.404419),
    "Arizona": (33.729759, -111.431221), "Arkansas": (34.969704, -92.373123),
    "California": (36.116203, -119.681564), "Colorado": (39.059811, -105.311104),
    "Connecticut": (41.597782, -72.755371), "Delaware": (39.318523, -75.507141),
    "Florida": (27.766279, -81.686783), "Georgia": (33.040619, -83.643074),
    "Hawaii": (21.094318, -157.498337), "Idaho": (44.240459, -114.478828),
    "Illinois": (40.349457, -88.986137), "Indiana": (39.849426, -86.258278),
    "Iowa": (42.011539, -93.210526), "Kansas": (38.526600, -96.726486),
    "Kentucky": (37.668140, -84.670067), "Louisiana": (31.169546, -91.867805),
    "Maine": (44.693947, -69.381927), "Maryland": (39.063946, -76.802101),
    "Massachusetts": (42.230171, -71.530106), "Michigan": (43.326618, -84.536095),
    "Minnesota": (45.694454, -93.900192), "Mississippi": (32.741646, -89.678696),
    "Missouri": (38.456085, -92.288368), "Montana": (46.921925, -110.454353),
    "Nebraska": (41.125370, -98.268082), "Nevada": (38.313515, -117.055374),
    "New Hampshire": (43.452492, -71.563896), "New Jersey": (40.298904, -74.521011),
    "New Mexico": (34.840515, -106.248482), "New York": (42.165726, -74.948051),
    "North Carolina": (35.630066, -79.806419), "North Dakota": (47.528912, -99.784012),
    "Ohio": (40.388783, -82.764915), "Oklahoma": (35.565342, -96.928917),
    "Oregon": (44.572021, -122.070938), "Pennsylvania": (40.590752, -77.209755),
    "Rhode Island": (41.680893, -71.511780), "South Carolina": (33.856892, -80.945007),
    "South Dakota": (44.299782, -99.438828), "Tennessee": (35.747845, -86.692345),
    "Texas": (31.054487, -97.563461), "Utah": (40.150032, -111.862434),
    "Vermont": (44.045876, -72.710686), "Virginia": (37.769337, -78.169968),
    "Washington": (47.400902, -121.490494), "West Virginia": (38.491226, -80.954453),
    "Wisconsin": (44.268543, -89.616508), "Wyoming": (42.755966, -107.302490),
}


def load_existing():
    if CACHE_JSON.exists():
        try:
            return json.loads(CACHE_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"created": None, "states": {}, "errors": {}}


def seed_from_training():
    """Read the training CSV with explicit column-name handling."""
    if not TRAINING_CSV.exists():
        print(f"  [seed] {TRAINING_CSV} not found — skipping")
        return {}

    df = pd.read_csv(TRAINING_CSV)
    print(f"  [seed] loaded {TRAINING_CSV.name}: {len(df)} rows, "
          f"cols={list(df.columns)}")

    # Handle multiple possible column names
    state_col = next((c for c in ["_STATE", "STATE", "state"] if c in df.columns), None)
    year_col  = next((c for c in ["YEAR", "year"] if c in df.columns), None)
    aqi_col   = next((c for c in ["AQI_AVG", "AQI", "aqi", "aqi_avg"] if c in df.columns), None)
    pm_col    = next((c for c in ["PM25_AVG", "PM25", "pm25", "pm25_avg"] if c in df.columns), None)

    if not all([state_col, year_col, aqi_col, pm_col]):
        print(f"  [seed] MISSING expected columns. "
              f"found state={state_col}, year={year_col}, "
              f"aqi={aqi_col}, pm25={pm_col}")
        return {}

    seeded = {}
    for code, grp in df.groupby(state_col):
        name = STATE_NAMES.get(int(code))
        if not name:
            continue
        grp = grp.sort_values(year_col).tail(YEARS)
        if len(grp) >= 1:
            seeded[name] = {
                "aqi_5yr": float(grp[aqi_col].mean()),
                "pm25_5yr": float(grp[pm_col].mean()),
                "source": "training_csv",
                "years_covered": len(grp),
            }
    print(f"  [seed] extracted {len(seeded)} states")
    return seeded


def fetch_one_year(lat, lon, year):
    """Fetch a single year. Returns (avg_dict, error_msg)."""
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}&hourly=us_aqi,pm2_5"
        f"&start_date={year}-01-01&end_date={year}-12-31"
        f"&timezone=America/New_York"
    )
    try:
        r = requests.get(url, timeout=45)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text[:120]}"
        hourly = r.json().get("hourly", {})
        aqi = [v for v in hourly.get("us_aqi", []) if v is not None]
        pm = [v for v in hourly.get("pm2_5", []) if v is not None]
        if not aqi or not pm:
            return None, f"empty (aqi={len(aqi)}, pm={len(pm)})"
        return {"aqi": sum(aqi) / len(aqi),
                "pm25": sum(pm) / len(pm)}, None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:100]}"


def fetch_state(name, lat, lon):
    """Fetch 5 years, one year at a time."""
    end_year = datetime.now().year
    years = [end_year - k for k in range(YEARS)]
    results, errors = [], []

    for year in years:
        res, err = fetch_one_year(lat, lon, year)
        if res:
            results.append(res)
        else:
            errors.append(f"{year}: {err}")
        time.sleep(DELAY_BETWEEN_REQUESTS)

    if not results:
        return None, " | ".join(errors)

    return {
        "aqi_5yr": sum(r["aqi"] for r in results) / len(results),
        "pm25_5yr": sum(r["pm25"] for r in results) / len(results),
        "source": "fetched",
        "years_covered": len(results),
    }, ("partial: " + " | ".join(errors)) if errors else None


def main():
    print("=" * 70)
    print("  AQI Cache Builder")
    print("=" * 70)

    CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)
    cache = load_existing()

    # Step 1: seed from training cache
    if not cache.get("states"):
        print("\n[1] Seeding from training cache...")
        seeded = seed_from_training()
        cache["states"] = seeded
        cache["errors"] = {}
        print(f"    → {len(seeded)} states seeded\n")
    else:
        print(f"\n[1] Existing cache has {len(cache['states'])} states — "
              f"keeping them\n")

    # Step 2: fetch missing
    missing = [name for name in COORDS if name not in cache["states"]]
    print(f"[2] {len(missing)} states need fetching")

    if missing:
        print(f"    Estimated time: {len(missing) * 5 * DELAY_BETWEEN_REQUESTS / 60:.1f} min\n")
        for i, name in enumerate(missing, 1):
            lat, lon = COORDS[name]
            print(f"  [{i:>2}/{len(missing)}] {name:<20}", end="", flush=True)
            result, err = fetch_state(name, lat, lon)
            if result:
                cache["states"][name] = result
                print(f"  ✓ AQI={result['aqi_5yr']:.1f} "
                      f"PM25={result['pm25_5yr']:.1f}")
            else:
                cache["errors"][name] = err
                print(f"  ✗ {err[:80]}")
                if name in cache["states"]:
                    del cache["states"][name]

            # save after every state (crash-safe)
            cache["created"] = datetime.now().isoformat()
            CACHE_JSON.write_text(
                json.dumps(cache, indent=2), encoding="utf-8"
            )

    # Summary
    print("\n" + "=" * 70)
    print(f"  CACHE COMPLETE")
    print("=" * 70)
    print(f"  States cached   : {len(cache['states'])}/50")
    print(f"  States failed   : {len(cache['errors'])}")
    print(f"  Saved to        : {CACHE_JSON}")

    if cache["errors"]:
        print(f"\n  Failed states:")
        for name, err in list(cache["errors"].items())[:5]:
            print(f"    {name}: {err[:100]}")
        if len(cache["errors"]) > 5:
            print(f"    ... and {len(cache['errors']) - 5} more")


if __name__ == "__main__":
    main()