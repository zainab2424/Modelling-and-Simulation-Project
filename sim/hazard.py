from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set
import random
from sim.building import BuildingGraph

@dataclass
class FireHazard:
    # Node where the fire initially starts
    ignition_node: int

    # Probability that fire spreads to a neighboring node each step
    spread_prob: float = 0.03

    # Rate at which danger increases at burning nodes
    growth_rate: float = 0.01

    # Rate at which danger decreases at non-burning nodes
    decay_rate: float = 0.01

    # Threshold above which edges may later be considered for blocking
    block_threshold: float = 0.85

    # Maximum cap for danger level
    max_danger: float = 1.0

    # Set of nodes currently on fire
    burning_nodes: Set[int] = field(default_factory=set)

    # Dictionary storing danger level for each node
    danger: Dict[int, float] = field(default_factory=dict)

    def initialize(self):
        # Start fire at the ignition node
        self.burning_nodes = {self.ignition_node}

        # Assign initial danger value to ignition point
        self.danger = {self.ignition_node: 0.3}

    def step(self, g: BuildingGraph, rng: random.Random):
        # Increase danger level for all currently burning nodes
        for n in list(self.burning_nodes):
            self.danger[n] = min(self.max_danger, self.danger.get(n, 0.0) + self.growth_rate)

        # Determine which neighboring nodes will catch fire next
        new_burning: Set[int] = set()
        for n in self.burning_nodes:
            for nb in g.neighbors(n):
                # Do not allow fire to spread into the exit
                if g.node_types.get(nb) == "exit":
                    continue
                # Spread fire probabilistically
                if nb not in self.burning_nodes and rng.random() < self.spread_prob:
                    new_burning.add(nb)

        # Add newly burning nodes and initialize their danger
        for nb in new_burning:
            self.burning_nodes.add(nb)
            self.danger[nb] = max(self.danger.get(nb, 0.0), 0.25)

        # Apply decay to nodes that are no longer burning
        for n in list(self.danger.keys()):
            if n not in self.burning_nodes:
                self.danger[n] = max(0.0, self.danger[n] - self.decay_rate)
                # Remove nodes with zero danger to keep dict clean
                if self.danger[n] <= 0.0:
                    del self.danger[n]

    def node_danger(self, node: int) -> float:
        # Return current danger level for a node (0 if not present)
        return self.danger.get(node, 0.0)
