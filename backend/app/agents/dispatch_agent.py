"""Dispatch Agent — TEAMMATE'S half (STUB).

>>> This is a placeholder. Your teammate owns the real Dispatch Agent: it contacts
>>> the shortlisted drivers (e.g. via Vapi voice calls), negotiates, and collects
>>> real bids. To integrate, replace the body of `negotiate_bids` (and/or this whole
>>> agent object) with the real implementation. The Order Agent only depends on the
>>> AGENT OBJECT named `dispatch_agent` and the `DispatchResult` return contract, so
>>> nothing on the Order/Resource side needs to change.

The stub fabricates plausible bids from the shortlist so the full Order ->
Resource -> Dispatch -> award flow can be demoed offline today.
"""

from __future__ import annotations

import os

from agents import Agent, function_tool

from app.contracts import Bid, DispatchResult, DriverCandidate, Load

_MODEL = os.getenv("ORDER_AGENT_MODEL", "gpt-4o-mini")


def _fake_bid(driver: DriverCandidate, load: Load) -> Bid:
    """Deterministic, plausible fake bid derived from the load + driver.

    No randomness (keeps demos reproducible). Price rises with distance-implied
    effort (lower match_score) and load weight; ETA scales the same way.
    """
    base = 250.0
    weight_component = load.weight_tons * 18.0
    # Worse-matched (farther) drivers ask for more and take longer.
    distance_penalty = (1.0 - driver.match_score) * 400.0
    price = round(base + weight_component + distance_penalty, 2)

    eta = round(6.0 + (1.0 - driver.match_score) * 30.0, 1)
    # A driver whose ETA blows the deadline declines.
    accepted = eta <= load.deadline_hours
    note = "" if accepted else f"Can't make the {load.deadline_hours}h deadline."

    return Bid(
        driver_id=driver.driver_id,
        name=driver.name,
        price_usd=price,
        eta_hours=eta,
        accepted=accepted,
        note=note,
    )


@function_tool
def negotiate_bids(load: Load, shortlist: list[DriverCandidate]) -> DispatchResult:
    """[STUB] Contact each shortlisted driver and collect their bid.

    Replace this with real outbound contact (Vapi/voice/Telegram) + negotiation.
    """
    bids = [_fake_bid(d, load) for d in shortlist]
    summary = (
        f"{load.shipper}: {load.weight_tons}t {load.pickup_state}->{load.dropoff_state}, "
        f"deadline {load.deadline_hours}h"
    )
    return DispatchResult(load_summary=summary, bids=bids)


dispatch_agent = Agent(
    name="Dispatch Agent",
    handoff_description="Contacts shortlisted drivers and collects their bids.",
    instructions=(
        "You are a freight dispatcher. Given a load and a shortlist of driver "
        "candidates, call `negotiate_bids` to contact them and collect bids. Return "
        "every bid, including declines, so the order can be awarded fairly. "
        "[This is a stub implementation for the demo.]"
    ),
    model=_MODEL,
    tools=[negotiate_bids],
)
