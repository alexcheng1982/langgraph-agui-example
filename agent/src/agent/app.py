import uvicorn
from fastapi import FastAPI
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph


checkpointer = InMemorySaver()


def build_graph() -> CompiledStateGraph:
    return create_agent(
        model="openai:gpt-4.1-mini",
        system_prompt="You are a cooking assistant that provides practical, safe, and concise cooking advice.",
        checkpointer=checkpointer,
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
