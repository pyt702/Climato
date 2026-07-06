import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.climato

# ── Collections ─────────────────────────────────────────────────────────────
locations_col            = db.locations
weather_daily_col        = db.weather_daily      # one doc per (location_id, date)
conversations_collection = db.conversations
weather_collection = db.weather # Legacy
