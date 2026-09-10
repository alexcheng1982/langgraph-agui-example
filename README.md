# LangGraph AG-UI Example

A full-stack demo that connects a LangChain/LangGraph cooking assistant to a CopilotKit chat UI.

## Repository Structure

- `agent/` - FastAPI + LangGraph backend agent
- `web/` - Next.js + CopilotKit frontend

## What This Repo Does

- The backend exposes an AG-UI compatible endpoint at `POST /agent`.
- The frontend hosts a CopilotKit runtime route at `/api/copilotkit`.
- That runtime route forwards chat requests to the backend agent URL.

## Human-in-the-loop shopping demo

Try a request such as: “Please buy 2 eggs, tomatoes, and garlic for me.” The
simulated shopping workflow demonstrates the complete pause → human decision →
resume pattern:

1. The agent calls the frontend `purchase_online` tool exposed through
   `CopilotKitMiddleware`.
2. CopilotKit renders an approval card in the chat and pauses the tool call.
3. **Confirm purchase** returns `{ "approved": true }` to the agent, after which
   the simulated order step runs.
4. **Cancel** returns a rejection and no order is placed.

No real store, payment provider, or external side effect is involved.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- npm
- OpenAI API key

## 1) Start the Agent API

From the `agent/` folder:

```bash
uv sync
export OPENAI_API_KEY=your_key_here
uv run cooking_agent
```

The agent starts on `http://127.0.0.1:8300`.

Quick check:

```bash
curl http://127.0.0.1:8300/health
```

Expected response:

```json
{"status":"ok"}
```

## 2) Start the Web App

From the `web/` folder:

```bash
npm install
export AGENT_URL=http://127.0.0.1:8300/agent
npm run dev
```

Open `http://localhost:3000`.

## Environment Variables

### Backend (`agent`)

- `OPENAI_API_KEY` (required)

### Frontend (`web`)

- `AGENT_URL` (optional)
  - Default: `http://localhost:8300/agent`
  - Set this when your backend runs on a different host/port.

## Scripts

### `agent/`

- `uv run agent` - start FastAPI server on `127.0.0.1:8300`

### `web/`

- `npm run dev` - start Next.js dev server
- `npm run build` - production build
- `npm run start` - start production server
- `npm run lint` - run ESLint

## API Endpoints

### Backend

- `GET /health`
- `POST /agent`

### Frontend Runtime

- `GET /api/copilotkit`
- `POST /api/copilotkit`

## Troubleshooting

- If the UI cannot reach the agent:
  - Ensure `uv run agent` is running.
  - Verify `AGENT_URL` points to the backend `/agent` endpoint.
- If model calls fail:
  - Confirm `OPENAI_API_KEY` is set in the backend shell.
- If port conflicts occur:
  - Stop processes using `3000` or `8300`, or run services on different ports and update `AGENT_URL`.
