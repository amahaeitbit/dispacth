"""FastAPI app exposing the Order Agent to the assistant-ui frontend.

The `/api/chat` endpoint runs the Order Agent (which orchestrates the Resource
Allocation Agent and the Dispatch Agent) and streams the run to the browser using
the assistant-stream data-stream protocol that assistant-ui understands natively.

Text deltas stream as the assistant's reply; each sub-agent / tool call is
surfaced as a tool-call in the UI so you can watch the orchestration live.
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

load_dotenv()  # read backend/.env before agents import their model config

from agents import Runner  # noqa: E402
from agents.stream_events import RunItemStreamEvent  # noqa: E402
from openai.types.responses import ResponseTextDeltaEvent  # noqa: E402
from assistant_stream import RunController, create_run  # noqa: E402
from assistant_stream.serialization import DataStreamResponse  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from app.agents.order_agent import order_agent  # noqa: E402
from app.db import init_db  # noqa: E402

app = FastAPI(title="Dispatch Order Agent")

# assistant-ui dev server runs on :3000; allow it to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db(seed=True)


class UIMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    # assistant-ui's custom adapter posts the running message list.
    messages: list[UIMessage]


def _to_agent_input(messages: list[UIMessage]) -> list[dict]:
    """Convert UI messages to the Agents SDK input-item format."""
    return [{"role": m.role, "content": m.content} for m in messages]


@app.post("/api/chat")
async def chat(request: ChatRequest) -> DataStreamResponse:
    agent_input = _to_agent_input(request.messages)

    async def run(controller: RunController) -> None:
        result = Runner.run_streamed(order_agent, input=agent_input)
        open_tool_calls: dict[str, object] = {}

        async for event in result.stream_events():
            # 1. Token-by-token assistant text.
            if event.type == "raw_response_event" and isinstance(
                event.data, ResponseTextDeltaEvent
            ):
                controller.append_text(event.data.delta)

            # 2. Tool / sub-agent invocations -> show them in the UI.
            elif isinstance(event, RunItemStreamEvent):
                item = event.item
                if item.type == "tool_call_item":
                    raw = item.raw_item
                    name = getattr(raw, "name", "tool")
                    call_id = getattr(raw, "call_id", None) or getattr(raw, "id", "")
                    args = getattr(raw, "arguments", "") or ""
                    tc = controller.add_tool_call(name, call_id)
                    try:
                        tc.append_args_text(args)
                    except Exception:
                        pass
                    open_tool_calls[call_id] = tc
                elif item.type == "tool_call_output_item":
                    call_id = getattr(item.raw_item, "call_id", "") if hasattr(
                        item, "raw_item"
                    ) else ""
                    tc = open_tool_calls.get(call_id)
                    if tc is not None:
                        output = item.output
                        tc.set_result(
                            output if isinstance(output, (str, dict, list)) else str(output)
                        )

    return DataStreamResponse(create_run(run))


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
