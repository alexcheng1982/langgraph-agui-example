"use client";

import { CopilotChat, useDefaultRenderTool } from "@copilotkit/react-core/v2";
import { IngredientsPanel } from "@/components/ingredients-panel";

export default function Home() {
  useDefaultRenderTool();
  return (
    <main className="h-screen overflow-hidden bg-[radial-gradient(circle_at_top,#f7efe4_0%,#efe4d1_32%,#dcc7aa_100%)] p-3 text-stone-900 sm:p-4 lg:p-5">
      <div className="mx-auto h-full max-w-7xl">
        <section className="h-full rounded-[2rem] border border-stone-900/10 bg-white/80 p-3 shadow-[0_30px_80px_rgba(97,69,42,0.12)] backdrop-blur">
          <div className="h-full min-h-0 overflow-hidden rounded-[1.4rem] border border-stone-200 bg-stone-50 flex">
            <div className="flex-1 min-w-0">
              <CopilotChat
                className="h-full"
                labels={{
                  modalHeaderTitle: "Cooking Assistant",
                  welcomeMessageText:
                    "Ask a question about cooking, recipes, or ingredients, and I'll do my best to help you out!",
                }}
              />
            </div>
            <div className="w-64 shrink-0 hidden sm:block">
              <IngredientsPanel />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
