## Setup

```bash
uv sync
```

## Start API Server

```bash
export OPENAI_API_KEY=your_key_here
uv run cooking_agent
```

By default, the agent also connects to the Food Recipe MCP server over streamable HTTP:

- MCP listing: `https://mcpservers.org/servers/aidatanordic/food-recipe-mcp`
- Default MCP endpoint: `https://recipes.aidatanorge.no/mcp`

Optional environment variables:

```bash
# Override MCP endpoint
export FOOD_RECIPE_MCP_URL=https://recipes.aidatanorge.no/mcp

# Disable MCP tool loading (agent still runs with local tools)
export FOOD_RECIPE_MCP_ENABLED=false
```

This command starts the FastAPI server at `http://127.0.0.1:8300`.

## Endpoints

- `GET /health`
- `POST /agent` (AG-UI LangGraph endpoint for the cooking assistant)

## Quick Check

```bash
curl http://127.0.0.1:8300/health
```
