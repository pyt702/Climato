from datetime import datetime, timezone
from core.database import (
    locations_col,
    weather_daily_col,
    conversations_collection,
    weather_collection
)
from utils import normalize_city_name

# Helpers

def _date_range(start: str, end: str) -> list[str]:
    from datetime import date, timedelta
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    return [(s + timedelta(days=i)).isoformat() for i in range((e - s).days + 1)]

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")



# Daily cache — simple lookup per city + date range

async def get_daily_weather(location_id: str, start_date: str, end_date: str) -> list[dict]:
    """
    Returns all non-stale weather_daily docs for this location_id in the given date range.
    """
    dates   = _date_range(start_date, end_date)
    now_iso = _now_iso()
    cursor  = weather_daily_col.find({
        "location_id": location_id,
        "date":        {"$in": dates},
        "expires_at":  {"$gt": now_iso},
    })
    docs = await cursor.to_list(length=500)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


async def get_location(city: str) -> dict | None:
    """
    Normalizes the city name and searches the locations collection.
    """
    normalized = normalize_city_name(city)
    doc = await locations_col.find_one({"aliases": normalized})
    if doc:
        doc["_id"] = str(doc["_id"])
        return doc
    return None


async def upsert_location(official_name: str, lat: float, lon: float, tz: str, country: str, requested_city: str) -> str:
    """
    Upserts a location and adds requested_city to aliases.
    Returns the stringified ObjectId.
    """
    normalized_alias = normalize_city_name(requested_city)
    
    # First see if it already exists by official name
    existing = await locations_col.find_one({"official_name": official_name})
    
    if existing:
        if normalized_alias not in existing.get("aliases", []):
            await locations_col.update_one(
                {"_id": existing["_id"]},
                {"$addToSet": {"aliases": normalized_alias}}
            )
        return str(existing["_id"])
    
    # Insert new
    result = await locations_col.insert_one({
        "official_name": official_name,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "country": country,
        "aliases": [normalized_alias]
    })
    return str(result.inserted_id)

async def upsert_daily_weather(records: list[dict]) -> None:
    """Upsert by (location_id, date)."""
    for rec in records:
        await weather_daily_col.update_one(
            {"location_id": rec["location_id"], "date": rec["date"]},
            {"$set": rec},
            upsert=True,
        )


# Conversations

async def setup_indexes():
    await conversations_collection.create_index("timestamp", expireAfterSeconds=600)

async def insert_conversation(conv_doc: dict):
    result = await conversations_collection.insert_one(conv_doc)
    return str(result.inserted_id)

async def get_recent_conversations(session_id: str, limit: int = 5):
    cursor = conversations_collection.find({"session_id": session_id}).sort("timestamp", 1)
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


# Legacy

async def get_weather(cities: list, dates: list):
    cursor = weather_collection.find({
        "city":         {"$in": [c.lower().strip() for c in cities]},
        "weather_date": {"$in": dates},
    })
    docs = await cursor.to_list(length=50)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


async def save_weather_records(records: list):
    if not records:
        return
    await weather_collection.insert_many(records)
    for doc in records:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
