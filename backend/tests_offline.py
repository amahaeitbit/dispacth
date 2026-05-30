"""Offline sanity checks for the deterministic core (no OpenAI key required).

Run:  .venv/bin/python tests_offline.py
"""

import os
import tempfile

# Point the DB at a throwaway file BEFORE importing anything that reads it.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DISPATCH_DB_PATH"] = _tmp.name

import importlib

import app.db as db
importlib.reload(db)

from app.contracts import Load
from app.agents import resource_agent as ra
from app.agents import dispatch_agent as da

# function_tool wraps our funcs; reach the original via .__wrapped__ if present.
shortlist = getattr(ra.shortlist_drivers, "__wrapped__", None) or ra._score_driver
negotiate = getattr(da.negotiate_bids, "__wrapped__", None)


def main() -> None:
    db.init_db(seed=True)
    drivers = db.list_active_drivers()
    assert len(drivers) == 8, f"expected 8 seed drivers, got {len(drivers)}"

    # A refrigerated TX->NV load: only reefers near TX should rank high.
    load = Load(
        pickup_state="TX",
        dropoff_state="NV",
        weight_tons=15.0,
        volume_cubic_m=60.0,
        deadline_hours=48.0,
        refrigerated=True,
        shipper="Costco",
    )

    candidates = [c for d in drivers if (c := ra._score_driver(d, load)) is not None]
    candidates.sort(key=lambda c: c.match_score, reverse=True)
    assert candidates, "expected at least one reefer candidate"
    assert all(c.truck_type.value == "reefer" for c in candidates), \
        "refrigerated load must only match reefers"
    top = candidates[0]
    assert top.current_state == "TX", f"closest reefer should win, got {top.current_state}"
    print(f"[ok] shortlist top = {top.name} ({top.current_state}) score={top.match_score}")

    # Bids: at least one acceptance within a generous deadline.
    bids = [da._fake_bid(c, load) for c in candidates]
    accepted = [b for b in bids if b.accepted]
    assert accepted, "expected at least one accepted bid under a 48h deadline"
    best = min(accepted, key=lambda b: b.price_usd)
    print(f"[ok] best bid = {best.name} ${best.price_usd} eta={best.eta_hours}h")

    # Tight deadline should cause far drivers to decline.
    tight = load.model_copy(update={"deadline_hours": 7.0})
    tight_bids = [da._fake_bid(c, tight) for c in candidates]
    assert any(not b.accepted for b in tight_bids) or len(tight_bids) <= 1, \
        "tight deadline should make some drivers decline"
    print("[ok] tight-deadline declines behave")

    print("\nALL OFFLINE TESTS PASSED")


if __name__ == "__main__":
    main()
