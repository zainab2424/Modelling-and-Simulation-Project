from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set
import random
from sim.building import BuildingGraph

@dataclass
class FireHazard:
    ignition_node: int
    spread_prob: float = 0.03
    growth_rate: float = 0.01
    decay_rate: float = 0.01
    block_threshold: float = 0.85
    max_danger: float = 1.0

    burning_nodes: Set[int] = field(default_factory=set)
    danger: Dict[int, float] = field(default_factory=dict)

    def initialize(self):
        self.burning_nodes = {self.ignition_node}
        self.danger = {self.ignition_node: 0.3}

    def step(self, g: BuildingGraph, rng: random.Random):
        for n in list(self.burning_nodes):
            self.danger[n] = min(self.max_danger, self.danger.get(n, 0.0) + self.growth_rate)

        new_burning: Set[int] = set()
        for n in self.burning_nodes:
            for nb in g.neighbors(n):
                if g.node_types.get(nb) == "exit":
                    continue
                if nb not in self.burning_nodes and rng.random() < self.spread_prob:
                    new_burning.add(nb)

        for nb in new_burning:
            self.burning_nodes.add(nb)
            self.danger[nb] = max(self.danger.get(nb, 0.0), 0.25)

        for n in list(self.danger.keys()):
            if n not in self.burning_nodes:
                self.danger[n] = max(0.0, self.danger[n] - self.decay_rate)
                if self.danger[n] <= 0.0:
                    del self.danger[n]

    def node_danger(self, node: int) -> float:
        return self.danger.get(node, 0.0)