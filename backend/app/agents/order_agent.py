"""Order Agent — the orchestrator and shipper-facing front door.

Flow (matches the hackathon minutes):
  1. Talk to the shipper, gather a complete Load.
  2. Call the Resource Allocation Agent (as a tool) -> driver shortlist.
  3. Call the Dispatch Agent (as a tool) with the load + shortlist -> bids.
  4. Pick the best accepted bid (lowest price that meets the deadline), record
     the order, and confirm back to the shipper.

The Order Agent stays in control the whole time — sub-agents are exposed as
tools (call-and-return), not handoffs (transfer-control).
"""

from __future__ import annotations

import os

from agents import Agent, function_tool

from app.agents.dispatch_agent import dispatch_agent
from app.agents.resource_agent import resource_agent
from app.db import record_order

_MODEL = os.getenv("ORDER_AGENT_MODEL", "gpt-4o-mini")


@function_tool
def award_order(
    shipper: str,
    pickup_state: str,
    dropoff_state: str,
    weight_tons: float,
    deadline_hours: float,
    awarded_driver_id: int,
    awarded_price_usd: float,
) -> str:
    """Persist the awarded order to the database and return a confirmation id."""
    order_id = record_order(
        shipper=shipper,
        pickup_state=pickup_state,
        dropoff_state=dropoff_state,
        weight_tons=weight_tons,
        deadline_hours=deadline_hours,
        awarded_driver_id=awarded_driver_id,
        awarded_price_usd=awarded_price_usd,
        status="awarded",
    )
    return f"Order #{order_id} awarded to driver {awarded_driver_id} at ${awarded_price_usd:.2f}."


INSTRUCTIONS = """\
You are the Order Agent for a freight dispatching company. You speak with shippers
(e.g. Walmart, Costco) who need loads moved between US states.

Your job, step by step:
1. Collect a complete load from the shipper. You need: pickup state, dropoff state,
   weight in tons, volume in cubic meters, delivery deadline in hours, whether the
   goods are refrigerated/perishable, and the shipper's company name. Ask concise
   follow-up questions for anything missing. Use two-letter state codes.
2. Once the load is complete, call `allocate_resources` with the load to get a
   ranked shortlist of candidate drivers.
3. Call `dispatch_to_drivers` with the load AND that shortlist to collect bids.
4. Choose the winning bid: among bids where accepted=true, pick the lowest price
   that still meets the deadline. If none are accepted, tell the shipper no driver
   could meet the load and suggest relaxing the deadline.
5. Call `award_order` to record the win, then confirm to the shipper in plain
   language: who got it, the price, and the ETA.

Be concise and businesslike. Always show your reasoning for the chosen driver.
Never fabricate drivers or bids — only use the tool results.
"""

order_agent = Agent(
    name="Order Agent",
    instructions=INSTRUCTIONS,
    model=_MODEL,
    tools=[
        resource_agent.as_tool(
            tool_name="allocate_resources",
            tool_description=(
                "Given a load, return a ranked shortlist of registered drivers that "
                "can carry it (by location proximity and capacity)."
            ),
        ),
        dispatch_agent.as_tool(
            tool_name="dispatch_to_drivers",
            tool_description=(
                "Given a load and a driver shortlist, contact those drivers and "
                "return their bids (price, ETA, accepted/declined)."
            ),
        ),
        award_order,
    ],
)
