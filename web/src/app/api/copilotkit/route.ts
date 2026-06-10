import {
  CopilotRuntime,
  EmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const agentUrl = process.env.AGENT_URL || "http://localhost:8000/agent";

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: agentUrl,
    }),
  },
});

const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
  endpoint: "/api/copilotkit",
  runtime,
  serviceAdapter: new EmptyAdapter(),
});

export const dynamic = "force-dynamic";
export const POST = handleRequest;
export const GET = handleRequest;
