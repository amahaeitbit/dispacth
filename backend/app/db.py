"""SQLite persistence for drivers and orders.

Tiny on purpose: the hackathon needs a real, queryable list of registered
drivers (the minutes were explicit that drivers register under the platform with
truck type, capacity, and current location) plus a place to log accepted orders.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_DB_PATH = Path(os.getenv("DISPATCH_DB_PATH", "dispatch.db"))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Yield a connection with row access by column name."""
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS drivers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    truck_type    TEXT    NOT NULL,   -- dry_van | reefer | flatbed
    capacity_tons REAL    NOT NULL,
    capacity_cubic_m REAL NOT NULL,
    current_state TEXT    NOT NULL,   -- two-letter state code
    active        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    shipper       TEXT    NOT NULL,
    pickup_state  TEXT    NOT NULL,
    dropoff_state TEXT    NOT NULL,
    weight_tons   REAL    NOT NULL,
    deadline_hours REAL   NOT NULL,
    awarded_driver_id INTEGER,
    awarded_price_usd REAL,
    status        TEXT    NOT NULL DEFAULT 'pending',  -- pending | awarded | failed
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# A small fleet spread across states so routing has something to reason about.
_SEED_DRIVERS = [
    # name,            truck_type, tons, cubic_m, state
    ("Carlos Mendez",  "dry_van", 20.0, 80.0, "TX"),
    ("Dwayne Brooks",  "reefer",  18.0, 70.0, "TX"),
    ("Priya Nair",     "flatbed", 25.0, 60.0, "NV"),
    ("Sam Whitfield",  "dry_van", 22.0, 85.0, "CA"),
    ("Lena Kowalski",  "reefer",  16.0, 65.0, "CA"),
    ("Marcus Lee",     "dry_van", 24.0, 90.0, "AZ"),
    ("Tanya Reyes",    "reefer",  19.0, 72.0, "IN"),
    ("Bjorn Aalto",    "flatbed", 28.0, 55.0, "WA"),
]


def init_db(seed: bool = True) -> None:
    """Create tables and (optionally) seed drivers if the fleet is empty."""
    with connect() as conn:
        conn.executescript(SCHEMA)
        if seed:
            count = conn.execute("SELECT COUNT(*) AS n FROM drivers").fetchone()["n"]
            if count == 0:
                conn.executemany(
                    "INSERT INTO drivers (name, truck_type, capacity_tons, "
                    "capacity_cubic_m, current_state) VALUES (?, ?, ?, ?, ?)",
                    _SEED_DRIVERS,
                )


def list_active_drivers() -> list[dict]:
    """Return every active driver as a plain dict."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, truck_type, capacity_tons, capacity_cubic_m, "
            "current_state FROM drivers WHERE active = 1"
        ).fetchall()
    return [dict(r) for r in rows]


def record_order(
    shipper: str,
    pickup_state: str,
    dropoff_state: str,
    weight_tons: float,
    deadline_hours: float,
    awarded_driver_id: int | None,
    awarded_price_usd: float | None,
    status: str,
) -> int:
    """Persist a finished order; returns the new order id."""
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO orders (shipper, pickup_state, dropoff_state, weight_tons, "
            "deadline_hours, awarded_driver_id, awarded_price_usd, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                shipper,
                pickup_state,
                dropoff_state,
                weight_tons,
                deadline_hours,
                awarded_driver_id,
                awarded_price_usd,
                status,
            ),
        )
        return int(cur.lastrowid)
