"""Shared data contracts for the dispatch system.

These models are the seam between the two halves of the project:

  * The **Order Agent** + **Resource Allocation Agent** (this repo) produce a
    ``Load`` and a shortlist of ``DriverCandidate`` objects.
  * The **Dispatch Agent** (teammate's half) consumes ``Load`` + the shortlist
    and returns a list of ``Bid`` objects.

Keep these stable. If the shape changes, both halves must agree.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TruckType(str, Enum):
    """Coarse truck categories drivers register under."""

    DRY_VAN = "dry_van"
    REEFER = "reefer"  # refrigerated — required for perishable / time-sensitive loads
    FLATBED = "flatbed"


class Load(BaseModel):
    """A shipment a shipper wants moved. Built by the Order Agent from the chat."""

    pickup_state: str = Field(..., description="Two-letter US state to pick up from, e.g. 'TX'.")
    dropoff_state: str = Field(..., description="Two-letter US state to deliver to, e.g. 'NV'.")
    weight_tons: float = Field(..., gt=0, description="Total load weight in tons.")
    volume_cubic_m: float = Field(..., gt=0, description="Total load volume in cubic meters.")
    deadline_hours: float = Field(
        ..., gt=0, description="Hours from now the load must be delivered within."
    )
    refrigerated: bool = Field(
        False, description="True if the goods are perishable and need a reefer truck."
    )
    shipper: str = Field(..., description="Name of the ordering company, e.g. 'Walmart'.")


class DriverCandidate(BaseModel):
    """A driver the Resource Allocation Agent considers a viable match for a load."""

    driver_id: int
    name: str
    truck_type: TruckType
    capacity_tons: float
    capacity_cubic_m: float
    current_state: str = Field(..., description="State the driver is currently in.")
    match_score: float = Field(
        ..., ge=0, le=1, description="0-1 fit score: location proximity + capacity headroom."
    )
    reason: str = Field(..., description="Short human-readable why-this-driver explanation.")


class Bid(BaseModel):
    """A price a driver offers for a load. Produced by the Dispatch Agent."""

    driver_id: int
    name: str
    price_usd: float
    eta_hours: float = Field(..., description="Driver's estimated hours to deliver.")
    accepted: bool = Field(..., description="Whether the driver agreed to take the load at all.")
    note: str = Field("", description="Any condition or comment from the driver.")


class DispatchResult(BaseModel):
    """What the Dispatch Agent returns to the Order Agent: all collected bids."""

    load_summary: str
    bids: list[Bid]
