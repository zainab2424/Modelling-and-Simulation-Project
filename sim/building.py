from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class Edge:
    src: int
    dst: int
    base_capacity: int
    base_travel_time: int
    blocked: bool = False
    slowdown: float = 1.0

    def effective_capacity(self) -> int:
        if self.blocked:
            return 0
        cap = int(max(1, round(self.base_capacity / self.slowdown)))
        return cap

    def effective_travel_time(self) -> int:
        if self.blocked:
            return 10**9
        return int(max(1, round(self.base_travel_time * self.slowdown)))

@dataclass
class BuildingGraph:
    edges: List[Edge] = field(default_factory=list)
    adj: Dict[int, List[int]] = field(default_factory=dict)
    node_types: Dict[int, str] = field(default_factory=dict)   # apt/corr/stair/exit
    floor_of_node: Dict[int, int] = field(default_factory=dict)

    def add_node(self, node_id: int, node_type: str, floor: int):
        self.node_types[node_id] = node_type
        self.floor_of_node[node_id] = floor
        self.adj.setdefault(node_id, [])

    def add_edge(self, src: int, dst: int, capacity: int, travel_time: int):
        e = Edge(src=src, dst=dst, base_capacity=capacity, base_travel_time=travel_time)
        idx = len(self.edges)
        self.edges.append(e)
        self.adj.setdefault(src, []).append(idx)

    def neighbors(self, node: int) -> List[int]:
        return [self.edges[i].dst for i in self.adj.get(node, [])]

def build_apartment_building(
    floors: int = 10,
    apts_per_floor: int = 10,
    stairwells: int = 2,
    corridor_capacity: int = 6,
    stair_capacity: int = 4,
    corridor_time: int = 1,
    stair_time: int = 1,
) -> Tuple[BuildingGraph, List[int], int]:
    """
    Graph:
      apartments -> corridor (per floor) -> stair landings (per stairwell per floor)
    Stairs connect downward to a single exit node.
    """
    g = BuildingGraph()
    node_id = 0

    exit_id = node_id
    g.add_node(exit_id, "exit", floor=0)
    node_id += 1

    apartment_nodes: List[int] = []
    corridor_nodes: List[int] = []
    stair_nodes: Dict[tuple[int, int], int] = {}

    for f in range(1, floors + 1):
        corr = node_id
        g.add_node(corr, "corr", floor=f)
        corridor_nodes.append(corr)
        node_id += 1

        for _ in range(apts_per_floor):
            apt = node_id
            g.add_node(apt, "apt", floor=f)
            apartment_nodes.append(apt)
            node_id += 1
            g.add_edge(apt, corr, capacity=corridor_capacity, travel_time=corridor_time)

        for s in range(stairwells):
            st = node_id
            g.add_node(st, "stair", floor=f)
            stair_nodes[(f, s)] = st
            node_id += 1
            g.add_edge(corr, st, capacity=stair_capacity, travel_time=corridor_time)

    for f in range(1, floors + 1):
        for s in range(stairwells):
            st_here = stair_nodes[(f, s)]
            if f == 1:
                g.add_edge(st_here, exit_id, capacity=stair_capacity, travel_time=stair_time)
            else:
                st_down = stair_nodes[(f - 1, s)]
                g.add_edge(st_here, st_down, capacity=stair_capacity, travel_time=stair_time)

    return g, apartment_nodes, exit_id