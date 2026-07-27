import asyncio
import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import InjectedToolCallId, tool
from langchain_core.messages import SystemMessage, ToolMessage
from typing import Annotated, Any, Callable
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

DEFAULT_FOOD_RECIPE_MCP_URL = "https://recipes.aidatanorge.no/mcp"
MODEL = os.getenv("MODEL", "openai:gpt-4.1-mini")

logger.info("Use model %s", MODEL)

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
        "You have access to a temperature conversion tool, an available ingredients tool, a recipe search MCP tool, and an ingredients update tool. "
        "Use the temperature tool whenever the user asks to convert temperatures between Celsius and Fahrenheit. "
        "Use the available ingredients tool whenever the user asks what ingredients are currently available. "
        "Use recipe search for recipe discovery or filtering requests. "
        "Use the update_ingredients tool whenever the user mentions or lists ingredients they have, want to use, or want to track — extract and save the selected ingredient list using that tool. "
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
        middleware=[IngredientsMiddleware()],
        tools=[convert_temperature, get_available_ingredients, update_ingredients, *mcp_tools],
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
