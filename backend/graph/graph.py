from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import (
    planner_node,
    clarification_node,
    database_node,
    weather_api_node,
    response_node,
)


def should_clarify(state: GraphState):
    return "clarification" if state.get("needs_clarification") else "database"


workflow = StateGraph(GraphState)

workflow.add_node("planner",       planner_node)
workflow.add_node("clarification", clarification_node)
workflow.add_node("database",      database_node)
workflow.add_node("weather_api",   weather_api_node)
workflow.add_node("response",      response_node)

workflow.set_entry_point("planner")

workflow.add_conditional_edges(
    "planner",
    should_clarify,
    {"clarification": "clarification", "database": "database"}
)

workflow.add_edge("clarification", END)
workflow.add_edge("database",      "weather_api")
workflow.add_edge("weather_api",   "response")
workflow.add_edge("response",      END)

app = workflow.compile()
