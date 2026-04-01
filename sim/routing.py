# sim/routing.py
from __future__ import annotations

from collections import deque
from typing import Dict, Optional, Set

from sim.building import BuildingGraph


def edge_between(g: BuildingGraph, src: int, dst: int) -> Optional[int]:
    """
    Return the edge index for the directed edge src -> dst, or None if not found.
    """
    # Iterate through all outgoing edges from src
    for eidx in g.adj.get(src, []):
        # Check if this edge leads to the desired destination
        if g.edges[eidx].dst == dst:
            return eidx
    return None  # No matching edge found


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
    # This allows us to run BFS starting from the goal backwards
    rev: Dict[int, list[int]] = {}
    for src, eidxs in g.adj.items():
        for eidx in eidxs:
            if eidx in blocked_edges:
                continue  # Skip edges explicitly marked as blocked
            e = g.edges[eidx]
            if e.blocked:
                continue  # Skip edges blocked by hazard
            rev.setdefault(e.dst, []).append(e.src)

    # Initialize distances with the goal node at distance 0
    dist: Dict[int, int] = {goal: 0}
    q = deque([goal])  # BFS queue starting from goal

    # Standard BFS traversal
    while q:
        cur = q.popleft()
        cur_d = dist[cur]
        # Explore all nodes that can reach current node
        for prev in rev.get(cur, []):
            if prev not in dist:
                dist[prev] = cur_d + 1  # One more hop away
                q.append(prev)

    return dist  # Contains only reachable nodes


def shortest_path_next_hop(g: BuildingGraph, start: int, goal: int, blocked_edges: Set[int]) -> Optional[int]:
    """
    Legacy helper: BFS from start to goal (unweighted) returning the next hop node.
    Slower than compute_distances_to_goal for many agents. 
    """
    # If already at goal, no movement needed
    if start == goal:
        return None

    q = deque([start])  # BFS queue
    prev: Dict[int, Optional[int]] = {start: None}  # Track path

    # Perform BFS from start to goal
    while q:
        cur = q.popleft()
        for eidx in g.adj.get(cur, []):
            if eidx in blocked_edges:
                continue  # Skip blocked edges
            e = g.edges[eidx]
            if e.blocked:
                continue  # Skip dynamically blocked edges
            nxt = e.dst
            if nxt not in prev:
                prev[nxt] = cur  # Record how we reached this node
                if nxt == goal:
                    q.clear()  # Stop early once goal is found
                    break
                q.append(nxt)

    # If goal was never reached, no path exists
    if goal not in prev:
        return None

    # Backtrack from goal to find the first step from start
    node = goal
    while prev[node] is not None and prev[node] != start:
        node = prev[node]

    # Return the immediate next hop from start toward goal
    return node if prev[node] == start else goal
