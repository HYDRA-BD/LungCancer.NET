"""
aqi_cache.py — persistent 5-year AQI cache with prefetch.

Strategy:
  1. Check xgb/cat/lgb training caches first — seed from disk (0 network calls).
  2. For missing states, fetch year-by-year (5 small requests per state)
     in parallel with 3 workers + 0.3s delays (avoid rate limits).
  3. Save to artifacts/aqi_5yr_cache.json (24h TTL).
  4. Capture per-state error messages into the cache for debugging.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

CACHE_PATH = Path("artifacts/aqi_5yr_cache.json")
ERROR_LOG = Path("artifacts/aqi_errors.json")
CACHE_TTL_HOURS = 24
MAX_WORKERS = 3
DELAY_BETWEEN_YEARS = 0.3
YEARS_WINDOW = 5

# Check ALL three training caches (any could exist)
TRAINING_CACHE_PATHS = [
    Path("xgb/data/aqi_cache.csv"),
    Path("cat/data/aqi_cache.csv"),
    Path("lgb/data/aqi_cache.csv"),
]

STATE_CODE_TO_NAME = {
    1: "Alabama", 2: "Alaska", 4: "Arizona", 5: "Arkansas",
    6: "California", 8: "Colorado", 9: "Connecticut", 10: "Delaware",
    11: "Florida", 12: "Georgia", 15: "Hawaii", 16: "Idaho",
    17: "Illinois", 18: "Indiana", 19: "Iowa", 20: "Kansas",
    21: "Kentucky", 22: "Louisiana", 23: "Maine", 24: "Maryland",
    25: "Massachusetts", 26: "Michigan", 27: "Minnesota", 28: "Mississippi",
    29: "Missouri", 30: "Montana", 31: "Nebraska", 32: "Nevada",
    33: "New Hampshire", 34: "New Jersey", 35: "New Mexico", 36: "New York",
    37: "North Carolina", 38: "North Dakota", 39: "Ohio", 40: "Oklahoma",
    41: "Oregon", 42: "Pennsylvania", 44: "Rhode Island", 45: "South Carolina",
    46: "South Dakota", 47: "Tennessee", 48: "Texas", 49: "Utah",
    50: "Vermont", 51: "Virginia", 53: "Washington", 54: "West Virginia",
    55: "Wisconsin", 56: "Wyoming",
}


# ───────────────────────────── cache IO ─────────────────────────────
def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {"created": None, "states": {}, "errors": {}}
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            c = json.load(f)
            c.setdefault("errors", {})
            return c
    except Exception:
        return {"created": None, "states": {}, "errors": {}}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache["created"] = datetime.now().isoformat()
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def _is_fresh(cache: dict) -> bool:
    if not cache.get("created"):
        return False
    try:
        created = datetime.fromisoformat(cache["created"])
        return (datetime.now() - created) < timedelta(hours=CACHE_TTL_HOURS)
    except Exception:
        return False


# ───────────────────────────── training seed ─────────────────────────────
def _seed_from_training() -> dict:
    """Try each training cache file. Returns {state_name: {...}}."""
    for path in TRAINING_CACHE_PATHS:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"[aqi] training cache {path} unreadable: {e}")
            continue
        if not {"_STATE", "YEAR", "AQI_AVG", "PM25_AVG"}.issubset(df.columns):
            print(f"[aqi] training cache {path} missing expected columns")
            continue

        seeded: dict[str, dict] = {}
        for code, grp in df.groupby("_STATE"):
            name = STATE_CODE_TO_NAME.get(int(code))
            if not name:
                continue
            grp = grp.sort_values("YEAR").tail(YEARS_WINDOW)
            if len(grp) >= 3:
                seeded[name] = {
                    "aqi_5yr": float(grp["AQI_AVG"].mean()),
                    "pm25_5yr": float(grp["PM25_AVG"].mean()),
                    "source": f"training_cache:{path.name}",
                    "years_covered": len(grp),
                }
        if seeded:
            print(f"[aqi] seeded {len(seeded)} states from {path}")
            return seeded
    return {}


# ───────────────────────────── fetch ─────────────────────────────
def _fetch_one_year(lat: float, lon: float, year: int) -> tuple[dict | None, str | None]:
    """Fetch one year of hourly AQI/PM2.5. Returns (avg_dict, error_msg)."""
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}&hourly=us_aqi,pm2_5"
        f"&start_date={year}-01-01&end_date={year}-12-31"
        f"&timezone=America/New_York"
    )
    try:
        r = requests.get(url, timeout=45)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text[:150]}"
        hourly = r.json().get("hourly", {})
        aqi = [v for v in hourly.get("us_aqi", []) if v is not None]
        pm = [v for v in hourly.get("pm2_5", []) if v is not None]
        if not aqi or not pm:
            return None, f"empty data (aqi={len(aqi)}, pm25={len(pm)})"
        return {
            "aqi": sum(aqi) / len(aqi),
            "pm25": sum(pm) / len(pm),
            "n": len(aqi),
        }, None
    except requests.Timeout:
        return None, f"timeout (45s) for {year}"
    except requests.ConnectionError as e:
        return None, f"connection error: {str(e)[:100]}"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:100]}"


def _fetch_state(state_name: str, lat: float, lon: float,
                 end_year: int) -> tuple[str, dict | None, str | None]:
    """Fetch 5 years one year at a time. Returns (name, avg_dict, error_string)."""
    years = [end_year - k for k in range(YEARS_WINDOW)]
    results, errors = [], []
    for year in years:
        res, err = _fetch_one_year(lat, lon, year)
        if res:
            results.append(res)
        else:
            errors.append(f"{year}: {err}")
        time.sleep(DELAY_BETWEEN_YEARS)

    if not results:
        return state_name, None, " || ".join(errors)

    return state_name, {
        "aqi_5yr": sum(r["aqi"] for r in results) / len(results),
        "pm25_5yr": sum(r["pm25"] for r in results) / len(results),
        "source": "fetched",
        "years_covered": len(results),
    }, ("partial: " + " || ".join(errors) if errors else None)


# ───────────────────────────── public API ─────────────────────────────
def prefetch_all_states(states_dict: dict, force: bool = False,
                        progress_callback=None) -> dict:
    cache = _load_cache()

    if not force and _is_fresh(cache) and len(cache.get("states", {})) >= len(states_dict) * 0.9:
        if progress_callback:
            progress_callback(len(cache["states"]), len(cache["states"]),
                              "(cache)", "fresh")
        return cache

    states = dict(cache.get("states", {}))
    errors = dict(cache.get("errors", {}))

    # 1. Seed from training cache (offline, instant)
    if not states or force:
        seeded = _seed_from_training()
        if seeded:
            states.update(seeded)

    # 2. Fetch missing states (per-year, 3 workers)
    missing = [(name, lat, lon) for name, (lat, lon) in states_dict.items()
               if name not in states]

    if missing:
        print(f"[aqi] fetching {len(missing)} states "
              f"({YEARS_WINDOW} requests each, {MAX_WORKERS} workers)...")
        end_year = datetime.now().year
        done = 0
        total = len(missing)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = {ex.submit(_fetch_state, name, lat, lon, end_year): name
                       for name, lat, lon in missing}
            for fut in as_completed(futures):
                name, result, err = fut.result()
                done += 1
                if result:
                    states[name] = result
                    errors.pop(name, None)
                    print(f"[aqi] {done}/{total} {name}: OK "
                          f"(aqi={result['aqi_5yr']:.1f}, "
                          f"years={result['years_covered']})")
                else:
                    errors[name] = err or "unknown error"
                    print(f"[aqi] {done}/{total} {name}: FAILED — {err}")
                if progress_callback:
                    progress_callback(done, total, name,
                                      "ok" if result else "failed")

    cache["states"] = states
    cache["errors"] = errors
    _save_cache(cache)

    if errors:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(ERROR_LOG, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2)
        print(f"[aqi] {len(errors)} state(s) failed — see {ERROR_LOG}")

    return cache


def get_state_aqi(cache: dict, state_name: str) -> dict | None:
    return cache.get("states", {}).get(state_name)


def cache_summary(cache: dict) -> str:
    n = len(cache.get("states", {}))
    err = len(cache.get("errors", {}))
    if not cache.get("created"):
        return f"{n} state(s) cached (never saved)"
    age_min = int((datetime.now() - datetime.fromisoformat(cache["created"])).total_seconds() / 60)
    suffix = f" · {err} failed" if err else ""
    return f"{n} state(s) cached · updated {age_min} min ago{suffix}"


def cache_is_complete(cache: dict, states_dict: dict) -> bool:
    return all(s in cache.get("states", {}) for s in states_dict)