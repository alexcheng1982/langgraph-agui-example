"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";

type CopilotProviderProps = {
  children: React.ReactNode;
};

export function CopilotProvider({ children }: CopilotProviderProps) {
  const enableInspector = process.env.NODE_ENV === "development";

  return (
    <CopilotKit runtimeUrl="/api/copilotkit" enableInspector={enableInspector}>
      {children}
    </CopilotKit>
  );
}
