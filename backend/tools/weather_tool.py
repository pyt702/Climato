"""
weather_tool.py

A. Geocoding       — city name → (lat, lon, timezone)
B. Endpoint Builder — WeatherTask → WeatherRequest
C. OpenMeteo Adapter — WeatherRequest → URL  (only place that knows Open-Meteo)
D. Batched Fetch    — one API call per city+range
"""

import httpx
import asyncio
from datetime import datetime, timezone, timedelta, date
from itertools import groupby
from schemas.dtos import WeatherTask, WeatherRequest
from repositories.weather_repo import get_location, upsert_location


# ---------------------------------------------------------------------------
# Fixed daily variables — always fetch the full set
# ---------------------------------------------------------------------------

DAILY_VARIABLES = (
    "temperature_2m_max,temperature_2m_min,"
    "apparent_temperature_max,apparent_temperature_min,"
    "weather_code,precipitation_sum,"
    "precipitation_probability_max,"
    "wind_speed_10m_max,wind_gusts_10m_max,"
    "uv_index_max,sunrise,sunset"
)


# ---------------------------------------------------------------------------
# Staleness helper — computed once at insert time
# ---------------------------------------------------------------------------

def compute_expires_at(record_date: str, data_type: str) -> str:
    if data_type == "historical":
        return "2099-12-31T23:59:59Z"   # never expires

    today = datetime.now(timezone.utc).date()
    days_away = (date.fromisoformat(record_date) - today).days
    delta = timedelta(hours=6) if days_away <= 2 else timedelta(hours=24)
    return (datetime.now(timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# A. Geocoding
# ---------------------------------------------------------------------------

async def get_coordinates(city: str, client: httpx.AsyncClient) -> tuple[str, float, float, str, str] | None:
    """Returns (official_name, latitude, longitude, timezone, country) or None if city not found."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        r = await client.get(url, timeout=10)
        r.raise_for_status()
        results = r.json().get("results")
        if not results:
            return None
        hit = results[0]
        return hit.get("name", city), hit["latitude"], hit["longitude"], hit.get("timezone", "auto"), hit.get("country", "")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# B. Endpoint Builder (no Open-Meteo knowledge)
# ---------------------------------------------------------------------------

def build_weather_request(task: WeatherTask, lat: float, lon: float, tz: str) -> WeatherRequest:
    return WeatherRequest(
        endpoint="archive" if task.type == "historical" else "forecast",
        city=task.city,
        latitude=lat,
        longitude=lon,
        timezone=tz,
        start_date=task.start_date,
        end_date=task.end_date,
    )


# ---------------------------------------------------------------------------
# C. OpenMeteo Adapter — the ONLY function that knows Open-Meteo
# ---------------------------------------------------------------------------

def build_url(req: WeatherRequest) -> str:
    base = (
        "https://archive-api.open-meteo.com/v1/archive"
        if req.endpoint == "archive"
        else "https://api.open-meteo.com/v1/forecast"
    )
    return (
        f"{base}?latitude={req.latitude}&longitude={req.longitude}"
        f"&daily={DAILY_VARIABLES}"
        f"&start_date={req.start_date}&end_date={req.end_date}"
        f"&timezone={req.timezone}"
    )


# ---------------------------------------------------------------------------
# D. Response parser — raw Open-Meteo JSON → one record per date
# ---------------------------------------------------------------------------

def _parse_daily_response(raw: dict, location_id: str, city_display_name: str, data_type: str) -> list[dict]:
    daily   = raw.get("daily", {})
    dates   = daily.get("time", [])
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    for i, d in enumerate(dates):
        forecast = {
            var: vals[i] if i < len(vals) else None
            for var, vals in daily.items()
            if var != "time"
        }
        records.append({
            "location_id": location_id,
            "city":        city_display_name, # Temporary UI help
            "date":        d,
            "type":        data_type,
            "forecast":    forecast,
            "fetched_at":  now_str,
            "expires_at":  compute_expires_at(d, data_type),
        })
    return records


# ---------------------------------------------------------------------------
# D. Batched Fetch
# ---------------------------------------------------------------------------

def _group_key(task: WeatherTask) -> tuple:
    return (task.city.lower().strip(), task.type, task.start_date, task.end_date)


async def fetch_weather_batch(tasks: list[WeatherTask], client: httpx.AsyncClient) -> list[dict]:
    """One geocoding lookup per unique city, one API call per city+range group."""

    # --- Geocoding pass: check locations DB first, fall back to API ---
    unique_cities = {t.city for t in tasks}
    location_map: dict[str, dict] = {}

    for requested_city in unique_cities:
        # 1. Try reading from locations DB
        cached_loc = await get_location(requested_city)
        if cached_loc:
            location_map[requested_city] = cached_loc
            continue

        # 2. New location — call the geocoding API once
        coords = await get_coordinates(requested_city, client)
        if coords:
            official_name, lat, lon, tz, country = coords
            # 3. Upsert to locations DB and get the location_id
            loc_id = await upsert_location(official_name, lat, lon, tz, country, requested_city)
            location_map[requested_city] = {
                "_id": loc_id,
                "official_name": official_name,
                "latitude": lat,
                "longitude": lon,
                "timezone": tz,
                "country": country
            }

    records: list[dict] = []

    for key, group in groupby(sorted(tasks, key=_group_key), key=_group_key):
        task = list(group)[0]   # all tasks in group are identical for batching purposes
        requested_city = task.city

        if requested_city not in location_map:
            records.append({"city": requested_city, "status": "error", "message": "City not found",
                            "start_date": task.start_date, "end_date": task.end_date})
            continue

        loc = location_map[requested_city]
        lat, lon, tz = loc["latitude"], loc["longitude"], loc["timezone"]
        url = build_url(build_weather_request(task, lat, lon, tz))

        try:
            resp = await client.get(url, timeout=15)
            resp.raise_for_status()
            records.extend(_parse_daily_response(resp.json(), loc["_id"], loc["official_name"], task.type))
        except Exception as e:
            records.append({"city": requested_city, "status": "error", "message": str(e),
                            "start_date": task.start_date, "end_date": task.end_date})

    return records
