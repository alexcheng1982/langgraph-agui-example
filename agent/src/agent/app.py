import uvicorn
from fastapi import FastAPI
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph


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


def build_graph() -> CompiledStateGraph:
    return create_agent(
        model="openai:gpt-4.1-mini",
        system_prompt=(
            "You are a cooking assistant that provides practical, safe, and concise cooking advice. "
            "You have access to a temperature conversion tool — use it whenever the user asks to "
            "convert temperatures between Celsius and Fahrenheit."
        ),
        tools=[convert_temperature],
        checkpointer=InMemorySaver(),
    )


app = FastAPI(title="LangGraph AG-UI Agent")

agui_agent = LangGraphAgent(
    name="cooking-agent",
    description="A simple LangGraph agent exposed over the AG-UI protocol.",
    graph=build_graph(),
)

add_langgraph_fastapi_endpoint(app, agui_agent, "/agent")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("agent.app:app", host="127.0.0.1", port=8000, reload=False)
