"""
graph/nodes.py

Flow:  planner → database → weather_api → response
                    ↓ (needs_clarification)
               clarification → END
"""

import os
import json
import asyncio
import httpx
from datetime import datetime, date, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import Optional

from graph.state import GraphState
from repositories.weather_repo import get_daily_weather, upsert_daily_weather, get_location
from tools.weather_tool import fetch_weather_batch
from schemas.dtos import WeatherTask

# Initialize the language model

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


# Define the expected output schema for the planner

class PlannerOutput(BaseModel):
    weather_tasks: list[WeatherTask] = Field(
        description=(
            "One WeatherTask per (city × date-range). "
            "Set type='historical' for past dates, 'forecast' for today or future. "
            "Always output ISO dates (YYYY-MM-DD). Calculate relative dates like "
            "'tomorrow' or 'next Friday' yourself based on today's date."
        )
    )
    needs_clarification: bool = Field(
        description="True only if the city or date is completely ambiguous."
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="The question to ask the user when needs_clarification is True."
    )


# Planner Node: Parses user intent and extracts weather tasks

def _format_history(history: list) -> str:
    if not history:
        return "No recent conversation history."
    
    formatted = []
    for entry in history:
        formatted.append(f"User: {entry.get('question')}\nAI: {entry.get('answer')}")
    return "\n\n".join(formatted)

async def planner_node(state: GraphState):
    today = datetime.now().strftime("%Y-%m-%d")
    history_text = _format_history(state.get("history", []))
    
    prompt = PromptTemplate.from_template(
        "You are the intent parser for a travel-planner weather assistant.\n"
        f"Today's date is {today}.\n\n"
        "Recent conversation history for context (e.g. for pronouns or missing locations):\n"
        "{history}\n\n"
        "Extract one WeatherTask per (city × date-range) from the user's question.\n"
        "Rules:\n"
        "- type='historical' for dates before today, 'forecast' for today or future.\n"
        "- For date ranges ('July 10 to July 15'), set start_date and end_date.\n"
        "- For a single date, set start_date = end_date.\n"
        "- Always use ISO format YYYY-MM-DD. Calculate relative dates yourself.\n\n"
        "Question: {question}"
    )

    structured_llm = llm.with_structured_output(PlannerOutput)
    chain = prompt | structured_llm

    try:
        result: PlannerOutput = await chain.ainvoke({"question": state["question"], "history": history_text})
        tasks = [t.model_dump() for t in result.weather_tasks]
        print("\nReached Planner Node")
        print(f"planner has planned these tasks  to solve the query : \"{state['question']}\"")
        for i, task in enumerate(tasks, 1):
            print(f"task {i}:")
            print(json.dumps(task, indent=2))
        return {
            "weather_tasks":          tasks,
            "needs_clarification":    result.needs_clarification,
            "clarification_question": result.clarification_question,
        }
    except Exception as e:
        print(f"[planner_node] Error: {e}")
        return {
            "weather_tasks":          [],
            "needs_clarification":    True,
            "clarification_question": "I had trouble understanding that. Could you rephrase?",
        }


# Clarification Node: Asks the user for missing details

async def clarification_node(state: GraphState):
    print(f"\n\033[91m\033[1m--- [Clarification Node] ---\033[0m Triggered. Question: {state.get('clarification_question')}")
    return {"final_answer": state.get("clarification_question", "Can you clarify your request?")}


# Database Node: Checks the local cache for weather data

def _date_range_list(start: str, end: str) -> list[str]:
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    return [(s + timedelta(days=i)).isoformat() for i in range((e - s).days + 1)]


async def database_node(state: GraphState):
    tasks = state.get("weather_tasks", [])
    tasks = state.get("weather_tasks", [])
    if not tasks:
        return {"db_results": [], "missing_tasks": []}

    db_results   = []
    missing_tasks = []

    for i, t in enumerate(tasks, 1):
        print(f"\ntask {i} reached DatabaseNode")
        loc = await get_location(t["city"])
        if loc:
            t["location_id"] = loc["_id"] # temporarily attach for DB lookup
            hits = await get_daily_weather(loc["_id"], t["start_date"], t["end_date"])
            
            # Attach the UI friendly city name back onto hits for the frontend
            for hit in hits:
                hit["city"] = loc["official_name"]
        else:
            hits = []

        found_dates = {doc["date"] for doc in hits}
        needed_dates = set(_date_range_list(t["start_date"], t["end_date"]))

        db_results.extend(hits)
        if needed_dates - found_dates:   # any date missing from cache?
            print(f"found results - {len(hits)} make a weather tool call")
            missing_tasks.append(t)
        else:
            print(f"found results - {len(hits)}")

    return {"db_results": db_results, "missing_tasks": missing_tasks}


# Weather API Node: Fetches missing data from the external API

async def weather_api_node(state: GraphState) -> dict:
    missing = state.get("missing_tasks", [])
    for i, t in enumerate(missing, 1):
        print(f"\ntask {i} Reached weather tool")
    if not missing:
        return {}

    db_results = list(state.get("db_results", []))

    async with httpx.AsyncClient() as client:
        api_records = await fetch_weather_batch([WeatherTask(**t) for t in missing], client)

    valid  = [r for r in api_records if r.get("status") != "error"]
    errors = [r for r in api_records if r.get("status") == "error"]

    if errors:
        print(f"[weather_api_node] {len(errors)} error(s): {errors}")

    if valid:
        await upsert_daily_weather(valid)
        db_results.extend(valid)

    return {"db_results": db_results, "api_results": valid}


# Response Node: Generates the final natural language answer

async def response_node(state: GraphState):
    history_text = _format_history(state.get("history", []))
    prompt = PromptTemplate.from_template(
        "You are Climato, a helpful AI Meteorologist for a travel planner.\n"
        "Recent conversation history for context:\n"
        "{history}\n\n"
        "Answer the user's question naturally based on the weather data below.\n"
        "If data is missing, politely say you couldn't retrieve it.\n"
        "If there is a lot of data, structure it nicely using markdown (e.g., bullet points or tables).\n\n"
        "Weather data:\n{data}\n\n"
        "Question: {question}\n\nAnswer:"
    )
    result = await (prompt | llm | StrOutputParser()).ainvoke({
        "question": state["question"],
        "data":     json.dumps(state.get("db_results", []), indent=2),
        "history":  history_text
    })
    print(f"\n\033[92m\033[1m--- [Response Node] ---\033[0m Final Answer generated successfully.\n")

    return {
        "final_answer": result,
        "db_results": state.get("db_results", [])
    }
