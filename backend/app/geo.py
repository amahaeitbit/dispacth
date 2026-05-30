"""Very small geography helper for proximity scoring.

This is intentionally a coarse approximation, not a real routing engine. We model
a handful of US states as a graph and use hop-distance as a stand-in for "how far
is this driver from the pickup". Good enough to make the Resource Allocation
Agent's ranking explainable in a demo; swap for a real distance matrix later.
"""

from __future__ import annotations

# Undirected adjacency among the states our seed fleet/loads use.
_ADJACENCY: dict[str, set[str]] = {
    "CA": {"NV", "AZ", "OR"},
    "NV": {"CA", "AZ", "UT", "OR"},
    "AZ": {"CA", "NV", "UT", "NM"},
    "TX": {"NM", "OK", "LA"},
    "NM": {"AZ", "TX", "CO"},
    "WA": {"OR", "ID"},
    "OR": {"CA", "NV", "WA", "ID"},
    "IN": {"IL", "OH", "MI", "KY"},
}


def hop_distance(a: str, b: str, max_hops: int = 4) -> int:
    """Breadth-first hop count between two states.

    Returns 0 if same state, the number of hops if reachable within ``max_hops``,
    or ``max_hops + 1`` as a "far / unknown" sentinel otherwise.
    """
    a, b = a.upper(), b.upper()
    if a == b:
        return 0

    seen = {a}
    frontier = {a}
    for hop in range(1, max_hops + 1):
        nxt: set[str] = set()
        for state in frontier:
            nxt |= _ADJACENCY.get(state, set())
        if b in nxt:
            return hop
        nxt -= seen
        if not nxt:
            break
        seen |= nxt
        frontier = nxt
    return max_hops + 1


def proximity_score(driver_state: str, pickup_state: str) -> float:
    """Map hop distance to a 0-1 score (closer is higher)."""
    hops = hop_distance(driver_state, pickup_state)
    # 0 hops -> 1.0, 1 -> 0.75, 2 -> 0.5, 3 -> 0.25, far -> 0.05
    return max(0.05, 1.0 - 0.25 * hops)
