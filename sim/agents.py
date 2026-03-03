from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import random
import numpy as np

@dataclass
class Agent:
    agent_id: int
    start_node: int
    reaction_time: int
    panic_susceptibility: float
    base_speed: float

    node: int = 0
    status: str = "waiting"          # waiting | moving | evacuated | stuck
    panic: float = 0.0              # 0..1
    evac_time: Optional[int] = None

    remaining_travel: int = 0
    moving_to: Optional[int] = None
    moving_edge_idx: Optional[int] = None

    def __post_init__(self):
        self.node = self.start_node

def create_agents(
    apartment_nodes: List[int],
    occupants_per_apartment: int,
    reaction_logn_mu: float,
    reaction_logn_sigma: float,
    susceptibility_alpha: float,
    susceptibility_beta: float,
    speed_mean: float,
    speed_std: float,
    rng: random.Random,
    np_rng: np.random.Generator
) -> List[Agent]:
    agents: List[Agent] = []
    aid = 0
    for apt in apartment_nodes:
        for _ in range(occupants_per_apartment):
            r = int(max(0, round(rng.lognormvariate(reaction_logn_mu, reaction_logn_sigma))))

            s = float(np_rng.beta(susceptibility_alpha, susceptibility_beta))

            sp = max(0.7, min(1.3, rng.gauss(speed_mean, speed_std)))

            agents.append(Agent(
                agent_id=aid,
                start_node=apt,
                reaction_time=r,
                panic_susceptibility=s,
                base_speed=sp
            ))
            aid += 1
    return agents