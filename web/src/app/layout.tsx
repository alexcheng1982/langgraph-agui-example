import type { Metadata } from "next";
import { CopilotProvider } from "@/components/copilot-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cooking Assistant",
  description: "Cooking assistant built with LangGraph and CopilotKit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        <CopilotProvider>{children}</CopilotProvider>
      </body>
    </html>
  );
}
