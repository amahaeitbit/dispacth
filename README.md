# Dispatch — Order Agent

A freight-dispatching multi-agent system (hackathon project). A shipper (Walmart,
Costco, …) places a load order in a chat UI; an **Order Agent** orchestrates a
**Resource Allocation Agent** and a **Dispatch Agent** to shortlist drivers,
collect bids, and award the load.

## Architecture

```
Shipper (assistant-ui chat)
        │
        ▼
   ┌──────────────┐   as_tool    ┌────────────────────────────┐
   │ Order Agent  │─────────────▶│ Resource Allocation Agent   │  ← this repo
   │ (orchestrator)│◀─────────────│  (shortlist drivers)        │
   └──────────────┘   returns    └────────────────────────────┘
        │
        │ as_tool (load + shortlist)
        ▼
   ┌────────────────────────────┐
   │   Dispatch Agent (STUB)     │  ← teammate's half; returns fake bids for now
   │ (contact drivers → bids)    │
   └────────────────────────────┘
        │ returns bids
        ▼
   Order Agent picks best accepted bid → records order → confirms to shipper
```

Sub-agents are composed with the OpenAI Agents SDK **agent-as-tool** pattern
(`.as_tool()`), so the Order Agent stays in control and reports back — it does not
hand off the conversation.

### Ownership / seam

| Part | Owner | File |
|------|-------|------|
| Order Agent (orchestrator) | this repo | `backend/app/agents/order_agent.py` |
| Resource Allocation Agent | this repo | `backend/app/agents/resource_agent.py` |
| Dispatch Agent + driver comms (Vapi/voice) | **teammate** | `backend/app/agents/dispatch_agent.py` (**stub**) |

The seam contract lives in `backend/app/contracts.py` (`Load`, `DriverCandidate`,
`Bid`, `DispatchResult`). To integrate the real dispatcher, replace the body of
`negotiate_bids` / the `dispatch_agent` object — nothing on the Order/Resource
side changes.

## Run it

### 1. Backend (FastAPI + Agents SDK)

```bash
cd backend
uv venv && uv pip install -e .          # or: uv pip install -r requirements
cp .env.example .env                    # add your OPENAI_API_KEY
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Offline core test (no API key needed):

```bash
.venv/bin/python tests_offline.py
```

### 2. Frontend (Next.js + assistant-ui)

```bash
cd frontend
npm install
npm run dev                             # http://localhost:3000
```

`next.config.mjs` proxies `/api/*` to the FastAPI backend on `:8000`, so the
browser stays same-origin (no CORS setup needed).

## Demo script

Open http://localhost:3000 and click the suggested order, or type:

> "I'm Costco. I need 15 tons of refrigerated goods moved from TX to NV within
> 48 hours. Volume is about 60 cubic meters."

The Order Agent will gather the load, call `allocate_resources` (reefer trucks
near TX rank highest), call `dispatch_to_drivers` to collect bids, pick the best
accepted bid, and confirm the award.

## Notes / stubs

- **Dispatch Agent** returns deterministic fake bids — teammate's real
  implementation (Vapi voice calls + negotiation) drops in behind the same contract.
- **Geography** (`app/geo.py`) is a coarse state-adjacency graph for proximity
  scoring, not a real routing engine.
- Drivers/orders persist in **SQLite** (`backend/dispatch.db`, auto-seeded).
