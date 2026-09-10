import {
  CopilotRuntime,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const agentUrl = process.env.AGENT_URL || "http://localhost:8300/agent";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: agentUrl,
    }),
  },
});

const handler = createCopilotRuntimeHandler({
  runtime,
  basePath: "/api/copilotkit",
});

export const dynamic = "force-dynamic";
export const GET = handler;
export const POST = handler;
