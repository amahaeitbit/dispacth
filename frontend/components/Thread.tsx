"use client";

import {
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
} from "@assistant-ui/react";

/**
 * Minimal, self-contained chat thread built on assistant-ui primitives so it has
 * no dependency on the styled-components bundle version. Renders the shipper
 * conversation with the Order Agent.
 */
export function Thread() {
  return (
    <ThreadPrimitive.Root
      style={{ display: "flex", flexDirection: "column", height: "100%" }}
    >
      <ThreadPrimitive.Viewport
        style={{ flex: 1, overflowY: "auto", padding: "20px", minHeight: 0 }}
      >
        <ThreadPrimitive.Empty>
          <div style={{ maxWidth: 560, margin: "10vh auto", opacity: 0.85 }}>
            <h2 style={{ margin: "0 0 8px" }}>Place a freight order</h2>
            <p style={{ margin: "0 0 16px", fontSize: 14, lineHeight: 1.5 }}>
              Tell the Order Agent what you need moved. It will shortlist drivers,
              collect bids, and award the load.
            </p>
            <ThreadPrimitive.Suggestion
              prompt="I'm Costco. I need 15 tons of refrigerated goods moved from TX to NV within 48 hours. Volume is about 60 cubic meters."
              method="replace"
              autoSend
              style={suggestionStyle}
            >
              “Costco: 15t refrigerated, TX → NV, within 48h”
            </ThreadPrimitive.Suggestion>
          </div>
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            AssistantMessage,
          }}
        />
      </ThreadPrimitive.Viewport>

      <ComposerPrimitive.Root style={composerRootStyle}>
        <ComposerPrimitive.Input
          placeholder="Describe your load…"
          style={composerInputStyle}
        />
        <ComposerPrimitive.Send style={sendStyle}>Send</ComposerPrimitive.Send>
      </ComposerPrimitive.Root>
    </ThreadPrimitive.Root>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root style={{ ...bubbleRow, justifyContent: "flex-end" }}>
      <div style={{ ...bubble, ...userBubble }}>
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root style={bubbleRow}>
      <div style={{ ...bubble, ...assistantBubble }}>
        <MessagePrimitive.Parts components={{ ToolGroup }} />
      </div>
    </MessagePrimitive.Root>
  );
}

/** Renders agent/tool calls as a compact labeled chip so orchestration is visible. */
function ToolGroup({ children }: { children?: React.ReactNode }) {
  return (
    <div
      style={{
        margin: "6px 0",
        padding: "6px 10px",
        borderRadius: 8,
        fontSize: 12,
        fontFamily: "ui-monospace, monospace",
        background: "color-mix(in srgb, currentColor 8%, transparent)",
      }}
    >
      {children}
    </div>
  );
}

const bubbleRow: React.CSSProperties = {
  display: "flex",
  margin: "10px 0",
  maxWidth: 760,
  marginInline: "auto",
  width: "100%",
};
const bubble: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 14,
  fontSize: 14,
  lineHeight: 1.5,
  maxWidth: "80%",
  whiteSpace: "pre-wrap",
};
const userBubble: React.CSSProperties = {
  background: "#2563eb",
  color: "white",
};
const assistantBubble: React.CSSProperties = {
  background: "color-mix(in srgb, currentColor 8%, transparent)",
};
const composerRootStyle: React.CSSProperties = {
  display: "flex",
  gap: 8,
  padding: "12px 20px",
  borderTop: "1px solid color-mix(in srgb, currentColor 12%, transparent)",
  maxWidth: 800,
  margin: "0 auto",
  width: "100%",
};
const composerInputStyle: React.CSSProperties = {
  flex: 1,
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid color-mix(in srgb, currentColor 20%, transparent)",
  background: "transparent",
  color: "inherit",
  fontSize: 14,
  resize: "none",
};
const sendStyle: React.CSSProperties = {
  padding: "0 16px",
  borderRadius: 10,
  border: "none",
  background: "#2563eb",
  color: "white",
  cursor: "pointer",
};
const suggestionStyle: React.CSSProperties = {
  display: "block",
  textAlign: "left",
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid color-mix(in srgb, currentColor 20%, transparent)",
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
  fontSize: 14,
};
