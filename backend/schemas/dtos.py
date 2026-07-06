from pydantic import BaseModel
from typing import Optional, List, Literal

class WeatherTask(BaseModel):
    """Produced by the Planner LLM. One task per (city × date-range) need."""
    type:       Literal["forecast", "historical"]
    city:       str
    start_date: str   # YYYY-MM-DD
    end_date:   str   # YYYY-MM-DD

class WeatherRequest(BaseModel):
    """Provider-agnostic intermediate object. Only the adapter reads this."""
    endpoint:  Literal["forecast", "archive"]
    city:      str
    latitude:  float
    longitude: float
    timezone:  str = "auto"
    start_date: str
    end_date:   str

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str
    data: Optional[List[dict]] = None
