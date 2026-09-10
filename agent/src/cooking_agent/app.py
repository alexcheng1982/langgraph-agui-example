import asyncio
import json
import logging
import os
import random

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
import mlflow
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import InjectedToolCallId, tool
from langchain_core.messages import SystemMessage, ToolMessage
from typing import Annotated
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from copilotkit import CopilotKitMiddleware


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

DEFAULT_FOOD_RECIPE_MCP_URL = "https://recipes.aidatanorge.no/mcp"
DEFAULT_MLFLOW_TRACKING_URI = "http://localhost:5000"
DEFAULT_MLFLOW_EXPERIMENT = "cooking-agent"
MODEL = os.getenv("MODEL", "openai:gpt-4.1-mini")

logger.info("Use model %s", MODEL)


def configure_mlflow() -> None:
    """Configure MLflow tracing before constructing the LangGraph agent."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", DEFAULT_MLFLOW_TRACKING_URI)
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", DEFAULT_MLFLOW_EXPERIMENT)

    mlflow.set_tracking_uri(tracking_uri)
    try:
        mlflow.set_experiment(experiment_name)
    except Exception as exc:  # pragma: no cover - depends on MLflow availability
        logger.warning("Unable to set MLflow experiment %s: %s", experiment_name, exc)

    # This enables automatic tracing for LangChain and LangGraph invocations.
    mlflow.langchain.autolog(silent=True)
    # This also captures OpenAI SDK calls made directly or underneath integrations.
    mlflow.openai.autolog(silent=True)
    logger.info("MLflow tracing enabled: %s (experiment=%s)", tracking_uri, experiment_name)


configure_mlflow()

class AgentState(MessagesState):
    available_ingredients: list[str]
    selected_ingredients: list[str]


@tool
def convert_temperature(value: float, from_scale: str, to_scale: str) -> str:
    """Convert a temperature value between scales.

    Args:
        value: The numeric temperature value to convert.
        from_scale: The source temperature scale. One of 'celsius' or 'fahrenheit'.
        to_scale: The target temperature scale. One of 'celsius' or 'fahrenheit'.

    Returns:
        A string describing the converted temperature.
    """
    from_scale = from_scale.lower().strip()
    to_scale = to_scale.lower().strip()

    # Normalise aliases
    scale_aliases = {
        "c": "celsius", "°c": "celsius",
        "f": "fahrenheit", "°f": "fahrenheit",
    }
    from_scale = scale_aliases.get(from_scale, from_scale)
    to_scale = scale_aliases.get(to_scale, to_scale)

    supported = {"celsius", "fahrenheit"}
    if from_scale not in supported or to_scale not in supported:
        return (
            f"Unsupported scale(s): '{from_scale}' or '{to_scale}'. "
            "Please use 'celsius' or 'fahrenheit'."
        )

    if from_scale == to_scale:
        return f"{value}°{from_scale[0].upper()} is already in {to_scale.capitalize()}."

    # Convert between Celsius and Fahrenheit
    if from_scale == "fahrenheit":
        result = (value - 32) * 5 / 9
    else:
        result = value * 9 / 5 + 32

    return (
        f"{value}°{from_scale[0].upper()} = {result:.2f}°{to_scale[0].upper()} "
        f"({from_scale.capitalize()} to {to_scale.capitalize()})"
    )


@tool
def get_item_prices(items: list[str], currency: str = "USD") -> str:
    """Assign random simulated unit prices to shopping items and calculate a total."""
    if not items:
        return json.dumps({"items": [], "total": 0, "currency": currency})

    priced_items = []
    total = 0.0
    for item in items:
        unit_price = round(random.uniform(1.50, 12.00), 2)
        total += unit_price
        priced_items.append({"item": item, "unit_price": unit_price, "currency": currency})

    return json.dumps({
        "items": priced_items,
        "total": round(total, 2),
        "currency": currency,
    })


@tool
def get_available_ingredients(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Return available ingredients and initialize the selected list if needed."""
    available_ingredients = [
        "chicken breast",
        "eggs",
        "tomatoes",
        "onions",
        "garlic",
        "potatoes",
        "carrots",
    ]
    update = {"available_ingredients": available_ingredients}
    if "selected_ingredients" not in state:
        update["selected_ingredients"] = available_ingredients
    return Command(update={
        **update,
        "messages": [ToolMessage(
            "Available ingredients state updated.",
            tool_call_id=tool_call_id,
        )],
    })


@tool
def update_ingredients(
    selected_ingredients: list[str],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Update the selected ingredients list in the agent state.

    Args:
        selected_ingredients: The list of ingredients selected for cooking.

    Returns:
        A Command that updates the agent state with the provided ingredients.
    """
    return Command(update={
        "selected_ingredients": selected_ingredients,
        "messages": [ToolMessage("Selected ingredients state updated.", tool_call_id=tool_call_id)],
    })


def build_graph() -> CompiledStateGraph:
    mcp_tools = load_food_recipe_mcp_tools()

    BASE_PROMPT = (
        "You are a cooking assistant that provides practical, safe, and concise cooking advice. "
        "You have access to a temperature conversion tool, an available ingredients tool, a recipe search MCP tool, an ingredients update tool, a simulated item pricing tool, and a simulated online shopping tool. "
        "Use the temperature tool whenever the user asks to convert temperatures between Celsius and Fahrenheit. "
        "Use the available ingredients tool whenever the user asks what ingredients are currently available. "
        "Use recipe search for recipe discovery or filtering requests. "
        "Use the update_ingredients tool whenever the user mentions or lists ingredients they have, want to use, or want to track — extract and save the selected ingredient list using that tool. "
        "IMPORTANT: Do NOT restate, enumerate, or echo the currently selected ingredients back to the user in your text responses. "
        "The selected ingredients are already displayed to the user in the UI, so repeating them is redundant. "
        "After updating the selected ingredients, simply confirm the change briefly without listing them out. "
        "When the user asks to buy, order, or shop for items, you MUST call the frontend purchase_online tool; do not answer with only a text confirmation. "
        "For online shopping requests, first use purchase_online to prepare the requested item list and total. "
        "Before calling purchase_online, call get_item_prices with the requested items and use its returned random unit prices and total. "
        "That tool always pauses for explicit human approval before simulating the purchase; never claim an order was placed before approval. "
        "IMPORTANT: The recipe search tool requires all query parameters to be in English. "
        "If the user's request is in another language, translate key terms (dishes, ingredients, cooking methods) "
        "to English before calling the recipe search tool."
    )

    def _inject_ingredients(request):
        ingredients = (request.state or {}).get("selected_ingredients") or []
        current_ingredients = ", ".join(ingredients) if ingredients else "none"
        content = (
            BASE_PROMPT
            + f"\n\nThe user currently has these selected ingredients: {current_ingredients}."
            + "\nThis selected ingredients list is authoritative. Ignore any ingredient lists "
            + "from earlier messages or tool results."
        )
        return request.override(system_message=SystemMessage(content=content))

    class IngredientsMiddleware(AgentMiddleware):
        def wrap_model_call(self, request, handler):
            return handler(_inject_ingredients(request))

        async def awrap_model_call(self, request, handler):
            return await handler(_inject_ingredients(request))

    return create_agent(
        model=MODEL,
        system_prompt=BASE_PROMPT,
        middleware=[IngredientsMiddleware(), CopilotKitMiddleware()],
        tools=[convert_temperature, get_available_ingredients, update_ingredients, get_item_prices, *mcp_tools],
        state_schema=AgentState,
        checkpointer=InMemorySaver(),
    )


def load_food_recipe_mcp_tools():
    enabled = os.getenv("FOOD_RECIPE_MCP_ENABLED", "true").strip().lower()
    if enabled in {"0", "false", "no", "off"}:
        return []

    mcp_url = os.getenv("FOOD_RECIPE_MCP_URL", DEFAULT_FOOD_RECIPE_MCP_URL).strip()
    if not mcp_url:
        logger.warning("FOOD_RECIPE_MCP_URL is empty, skipping MCP tool loading.")
        return []

    client = MultiServerMCPClient(
        {
            "food-recipe": {
                "transport": "streamable_http",
                "url": mcp_url,
            }
        }
    )

    try:
        return asyncio.run(client.get_tools(server_name="food-recipe"))
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        logger.warning("Unable to load Food Recipe MCP tools from %s: %s", mcp_url, exc)
        return []


app = FastAPI(title="LangGraph AG-UI Agent")

graph = build_graph()

agui_agent = LangGraphAgent(
    name="cooking-agent",
    description="A simple LangGraph agent exposed over the AG-UI protocol.",
    graph=graph,
)

add_langgraph_fastapi_endpoint(app, agui_agent, "/agent")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("cooking_agent.app:app", host="127.0.0.1", port=8300, reload=True)
