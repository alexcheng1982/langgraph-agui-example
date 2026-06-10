## Setup

```bash
uv sync
```

## Start API Server

```bash
export OPENAI_API_KEY=your_key_here
uv run agent
```

This command starts the FastAPI server at `http://127.0.0.1:8000`.

## Endpoints

- `GET /health`
- `POST /agent` (AG-UI LangGraph endpoint for the cooking assistant)

## Quick Check

```bash
curl http://127.0.0.1:8000/health
```
