# sim/routing.py
from __future__ import annotations

from collections import deque
from typing import Dict, Optional, Set

from sim.building import BuildingGraph


def edge_between(g: BuildingGraph, src: int, dst: int) -> Optional[int]:
    """
    Return the edge index for the directed edge src -> dst, or None if not found.
    """
    for eidx in g.adj.get(src, []):
        if g.edges[eidx].dst == dst:
            return eidx
    return None


def compute_distances_to_goal(g: BuildingGraph, goal: int, blocked_edges: Set[int]) -> Dict[int, int]:
    """
    Compute shortest-path hop distance from every reachable node to `goal` using BFS,
    while ignoring blocked edges.

    IMPORTANT:
    - Uses the *current* edge blocked states (Edge.blocked) and `blocked_edges` set.
    - Returns a dict: node_id -> distance_in_hops
    - Nodes not in the dict are not reachable from the goal (given current blockages).

    This is meant to be called ONCE per time step, then agents can route by choosing
    the neighbor with the smallest distance value.
    """
    # Build reverse adjacency list for *unblocked* edges: dst -> [src1, src2, ...]
    rev: Dict[int, list[int]] = {}
    for src, eidxs in g.adj.items():
        for eidx in eidxs:
            if eidx in blocked_edges:
                continue
            e = g.edges[eidx]
            if e.blocked:
                continue
            rev.setdefault(e.dst, []).append(e.src)

    dist: Dict[int, int] = {goal: 0}
    q = deque([goal])

    while q:
        cur = q.popleft()
        cur_d = dist[cur]
        for prev in rev.get(cur, []):
            if prev not in dist:
                dist[prev] = cur_d + 1
                q.append(prev)

    return dist


# (Optional) Keep this for debugging/compatibility; not needed if you switch to distance-based routing.
def shortest_path_next_hop(g: BuildingGraph, start: int, goal: int, blocked_edges: Set[int]) -> Optional[int]:
    """
    Legacy helper: BFS from start to goal (unweighted) returning the next hop node.
    Slower than compute_distances_to_goal for many agents. Kept for reference.
    """
    if start == goal:
        return None

    q = deque([start])
    prev: Dict[int, Optional[int]] = {start: None}

    while q:
        cur = q.popleft()
        for eidx in g.adj.get(cur, []):
            if eidx in blocked_edges:
                continue
            e = g.edges[eidx]
            if e.blocked:
                continue
            nxt = e.dst
            if nxt not in prev:
                prev[nxt] = cur
                if nxt == goal:
                    q.clear()
                    break
                q.append(nxt)

    if goal not in prev:
        return None

    node = goal
    while prev[node] is not None and prev[node] != start:
        node = prev[node]
    return node if prev[node] == start else goal