from typing import TypedDict, Optional, List, Dict, Any


class GraphState(TypedDict):
    session_id: str
    question: str
    history: list

    # Planner output
    weather_tasks:          List[Dict[str, Any]]   # List of WeatherTask dicts
    needs_clarification:    bool
    clarification_question: Optional[str]

    # DB node output
    db_results:    List[Dict[str, Any]]   # cache hits
    missing_tasks: List[Dict[str, Any]]   # cache misses → go to API

    # API node output
    api_results: List[Dict[str, Any]]

    # Final answer
    final_answer: Optional[str]
