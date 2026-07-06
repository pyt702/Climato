from pydantic import BaseModel
from typing import List, Literal

class LocationRecord(BaseModel):
    id: str             
    official_name: str
    latitude: float
    longitude: float
    timezone: str
    country: str
    aliases: List[str]


class WeatherDailyRecord(BaseModel):
    """One document per location + date in the weather_daily collection."""
    location_id: str           # Stringified ObjectId of the LocationRecord
    date:      str              # "YYYY-MM-DD"
    type:      Literal["forecast", "historical"]
    forecast:  dict             # all daily variable values
    fetched_at: str            
    expires_at: str            
