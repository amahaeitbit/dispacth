"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useDataStreamRuntime } from "@assistant-ui/react-data-stream";
import { Thread } from "@/components/Thread";

export default function Home() {
  // Speaks the same data-stream protocol our FastAPI backend emits via
  // assistant-stream. `/api/chat` is proxied to FastAPI by next.config.mjs.
  const runtime = useDataStreamRuntime({ api: "/api/chat" });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="app-shell">
        <header className="app-header">
          <h1>Dispatch — Order Agent</h1>
          <p>Shipper console · place a freight order and watch the agents work</p>
        </header>
        <div className="thread-wrap">
          <Thread />
        </div>
      </div>
    </AssistantRuntimeProvider>
  );
}
