"""Resource Allocation Agent — YOUR half.

Given a load, it shortlists drivers from the registered fleet by location
proximity and capacity headroom. It returns candidates; it does NOT contact
drivers (that's the Dispatch Agent's job).
"""

from __future__ import annotations

import os

from agents import Agent, function_tool

from app.contracts import DriverCandidate, Load, TruckType
from app.db import list_active_drivers
from app.geo import proximity_score

_MODEL = os.getenv("ORDER_AGENT_MODEL", "gpt-4o-mini")


def _score_driver(driver: dict, load: Load) -> DriverCandidate | None:
    """Score one driver against a load. Returns None if the driver can't carry it."""
    # Hard constraints first: capacity and reefer requirement.
    if driver["capacity_tons"] < load.weight_tons:
        return None
    if driver["capacity_cubic_m"] < load.volume_cubic_m:
        return None
    if load.refrigerated and driver["truck_type"] != TruckType.REEFER.value:
        return None

    prox = proximity_score(driver["current_state"], load.pickup_state)

    # Capacity headroom: prefer a truck that fits without wild over-capacity,
    # but never penalize below the location signal too hard. Normalized 0-1.
    headroom = load.weight_tons / driver["capacity_tons"]  # 0..1, higher = tighter fit
    capacity_fit = 0.5 + 0.5 * headroom  # reward using the truck well

    score = round(0.7 * prox + 0.3 * capacity_fit, 3)

    reason = (
        f"{driver['current_state']} is {_dist_word(prox)} the {load.pickup_state} pickup; "
        f"{driver['truck_type']} carries {driver['capacity_tons']}t "
        f"(load is {load.weight_tons}t)."
    )
    return DriverCandidate(
        driver_id=driver["id"],
        name=driver["name"],
        truck_type=TruckType(driver["truck_type"]),
        capacity_tons=driver["capacity_tons"],
        capacity_cubic_m=driver["capacity_cubic_m"],
        current_state=driver["current_state"],
        match_score=score,
        reason=reason,
    )


def _dist_word(prox: float) -> str:
    if prox >= 0.9:
        return "at"
    if prox >= 0.7:
        return "next to"
    if prox >= 0.4:
        return "near"
    return "far from"


@function_tool
def shortlist_drivers(load: Load, top_n: int = 4) -> list[DriverCandidate]:
    """Rank registered drivers for a load and return the best ``top_n`` candidates.

    Filters out any driver that physically cannot carry the load (capacity or
    reefer requirement), then ranks the rest by location proximity + capacity fit.
    """
    drivers = list_active_drivers()
    scored = [c for d in drivers if (c := _score_driver(d, load)) is not None]
    scored.sort(key=lambda c: c.match_score, reverse=True)
    return scored[:top_n]


resource_agent = Agent(
    name="Resource Allocation Agent",
    handoff_description="Shortlists registered drivers for a load by location and capacity.",
    instructions=(
        "You allocate fleet resources to freight loads. Given a load, call "
        "`shortlist_drivers` to get ranked driver candidates. Return the shortlist "
        "with a one-line rationale per driver. Do NOT invent drivers or contact them — "
        "only rank the registered fleet. If no driver can carry the load, say so plainly."
    ),
    model=_MODEL,
    tools=[shortlist_drivers],
)
