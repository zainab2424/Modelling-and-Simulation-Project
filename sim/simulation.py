# sim/simulation.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import random
import numpy as np

from sim.building import BuildingGraph
from sim.agents import Agent, create_agents
from sim.hazard import FireHazard
from sim.routing import edge_between, compute_distances_to_goal


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class SimConfig:
    time_limit: int = 600

    # agent distributions
    reaction_logn_mu: float = 2.0
    reaction_logn_sigma: float = 0.55
    susceptibility_alpha: float = 2.0
    susceptibility_beta: float = 2.5
    speed_mean: float = 1.0
    speed_std: float = 0.10

    # panic dynamics
    panic_enabled: bool = True
    panic_from_hazard_weight: float = 0.65
    panic_from_neighbors_weight: float = 0.45
    panic_decay: float = 0.02
    panic_threshold_move_change: float = 0.55  # above this: more likely to make mistakes

    # hazard effects
    slowdown_per_danger: float = 2.0
    block_prob_when_high: float = 0.10


def simulate_one_run(
    g: BuildingGraph,
    apartment_nodes: List[int],
    exit_id: int,
    cfg: SimConfig,
    seed: int,
    occupants_per_apartment: int = 2,
    ignition_floor: Optional[int] = None,
) -> Dict:
    rng = random.Random(seed)

    # ---- Create agents
    agents: List[Agent] = create_agents(
        apartment_nodes=apartment_nodes,
        occupants_per_apartment=occupants_per_apartment,
        reaction_logn_mu=cfg.reaction_logn_mu,
        reaction_logn_sigma=cfg.reaction_logn_sigma,
        susceptibility_alpha=cfg.susceptibility_alpha,
        susceptibility_beta=cfg.susceptibility_beta,
        speed_mean=cfg.speed_mean,
        speed_std=cfg.speed_std,
        rng=rng,
    )

    # ---- Choose ignition node (corridor on ignition floor)
    max_floor = max(g.floor_of_node.values()) if g.floor_of_node else 1
    if ignition_floor is None:
        ignition_floor = rng.randint(1, max(1, max_floor))

    corridor_candidates = [
        n for n, t in g.node_types.items()
        if t == "corr" and g.floor_of_node[n] == ignition_floor
    ]
    ignition_node = rng.choice(corridor_candidates) if corridor_candidates else rng.choice(apartment_nodes)

    hazard = FireHazard(ignition_node=ignition_node)
    hazard.initialize()

    # ---- Queue model: for each edge, a FIFO queue of agent_ids waiting to enter
    edge_queues: Dict[int, List[int]] = {i: [] for i in range(len(g.edges))}

    # ---- Metrics
    max_queue_len_per_edge: Dict[int, int] = {i: 0 for i in range(len(g.edges))}
    total_queue_time = 0
    bottleneck_events = 0

    # ---- Dynamic blocked edges set
    dynamic_blocked_edges: Set[int] = set()

    def compute_node_occupancy() -> Dict[int, List[int]]:
        occ: Dict[int, List[int]] = {}
        for a in agents:
            if a.status in ("waiting", "moving", "stuck"):
                occ.setdefault(a.node, []).append(a.agent_id)
        return occ

    # ========== Main simulation loop ==========
    for t in range(cfg.time_limit):
        # 1) Update hazard
        hazard.step(g, rng)

        # 2) Update edge slowdown/blocking based on danger
        dynamic_blocked_edges.clear()
        for eidx, e in enumerate(g.edges):
            src_d = hazard.node_danger(e.src)
            dst_d = hazard.node_danger(e.dst)
            danger = max(src_d, dst_d)

            # slowdown increases with danger
            e.slowdown = 1.0 + danger * cfg.slowdown_per_danger

            # probabilistic blocking when danger is high
            if danger >= hazard.block_threshold and rng.random() < cfg.block_prob_when_high:
                e.blocked = True

            # allow recovery sometimes if not too dangerous
            if danger < 0.35 and e.blocked and rng.random() < 0.15:
                e.blocked = False

            if e.blocked:
                dynamic_blocked_edges.add(eidx)

        # 3) Compute distance-to-exit map ONCE per timestep (fast routing)
        dist_to_exit = compute_distances_to_goal(g, exit_id, dynamic_blocked_edges)

        # 4) Panic update (hazard proximity + nearby panic)
        node_occ = compute_node_occupancy()

        def hazard_signal(node: int) -> float:
            s0 = hazard.node_danger(node)
            s1 = 0.0
            for nb in g.neighbors(node):
                s1 = max(s1, hazard.node_danger(nb))
            return clamp01(max(s0, 0.7 * s1))

        node_panic_avg: Dict[int, float] = {}
        for n, ids in node_occ.items():
            node_panic_avg[n] = float(np.mean([agents[i].panic for i in ids])) if ids else 0.0

        for a in agents:
            if a.status == "evacuated":
                continue

            if not cfg.panic_enabled:
                a.panic = 0.0
                continue

            hz = hazard_signal(a.node)
            neigh = node_panic_avg.get(a.node, 0.0)

            target = (cfg.panic_from_hazard_weight * hz + cfg.panic_from_neighbors_weight * neigh) * (
                0.35 + 0.65 * a.panic_susceptibility
            )
            # smooth-ish update + slight decay
            a.panic = clamp01(max(a.panic - cfg.panic_decay, 0.0) + 0.25 * target)

        # 5) Advance in-transit agents
        for a in agents:
            if a.status == "moving":
                a.remaining_travel -= 1
                if a.remaining_travel <= 0:
                    a.node = a.moving_to if a.moving_to is not None else a.node
                    a.status = "waiting"
                    a.moving_to = None
                    a.moving_edge_idx = None
                    a.remaining_travel = 0

        # 6) For waiting agents: pick next hop and join edge queue
        for a in agents:
            if a.status in ("evacuated", "stuck", "moving"):
                continue
            if t < a.reaction_time:
                continue  # still reacting

            if a.node == exit_id:
                a.status = "evacuated"
                a.evac_time = t
                continue

            # If node isn't reachable to exit right now, agent is stuck
            if a.node not in dist_to_exit:
                a.status = "stuck"
                continue

            # Choose neighbor with smallest distance to exit (greedy step)
            candidates: List[tuple[int, int]] = []  # (dist, neighbor)
            for nb in g.neighbors(a.node):
                eidx2 = edge_between(g, a.node, nb)
                if eidx2 is None:
                    continue
                if eidx2 in dynamic_blocked_edges or g.edges[eidx2].blocked:
                    continue
                if nb in dist_to_exit:
                    candidates.append((dist_to_exit[nb], nb))

            if not candidates:
                a.status = "stuck"
                continue

            candidates.sort(key=lambda x: x[0])
            next_hop = candidates[0][1]

            # Panic-driven poorer decisions: sometimes choose a random *reachable* neighbor
            if cfg.panic_enabled and a.panic >= cfg.panic_threshold_move_change:
                if rng.random() < 0.20 + 0.25 * a.panic:
                    reachable_nbs = [nb for (_, nb) in candidates]
                    if reachable_nbs:
                        next_hop = rng.choice(reachable_nbs)

            eidx = edge_between(g, a.node, next_hop)
            if eidx is None:
                a.status = "stuck"
                continue

            # Join queue (avoid duplicates)
            if a.agent_id not in edge_queues[eidx]:
                edge_queues[eidx].append(a.agent_id)

        # 7) Process edge queues (capacity limits)
        for eidx, q in list(edge_queues.items()):
            e = g.edges[eidx]
            cap = e.effective_capacity()

            if cap <= 0:
                max_queue_len_per_edge[eidx] = max(max_queue_len_per_edge[eidx], len(q))
                continue

            if len(q) >= 10:
                bottleneck_events += 1

            max_queue_len_per_edge[eidx] = max(max_queue_len_per_edge[eidx], len(q))

            to_move = q[:cap]
            edge_queues[eidx] = q[cap:]

            for aid in to_move:
                ag = agents[aid]
                # Only move if agent is still at the edge source and waiting
                if ag.status == "waiting" and ag.node == e.src:
                    ag.status = "moving"
                    ag.moving_to = e.dst
                    ag.moving_edge_idx = eidx
                    travel = max(1, int(round(e.effective_travel_time() / ag.base_speed)))
                    ag.remaining_travel = travel

            total_queue_time += len(edge_queues[eidx])

        # 8) Mark evacuated (in case someone arrives exactly on exit node this step)
        for a in agents:
            if a.status != "evacuated" and a.node == exit_id:
                a.status = "evacuated"
                a.evac_time = t

        # Early stop if all evacuated
        if all(a.status == "evacuated" for a in agents):
            break

    # ---- Collect results
    evac_times = [a.evac_time for a in agents if a.evac_time is not None]
    not_evacuated = sum(1 for a in agents if a.status != "evacuated")
    bottlenecks = sorted(max_queue_len_per_edge.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "seed": seed,
        "ignition_floor": ignition_floor,
        "agents": len(agents),
        "evacuated": len(evac_times),
        "not_evacuated": not_evacuated,
        "mean_evac_time": float(np.mean(evac_times)) if evac_times else float("nan"),
        "p50_evac_time": float(np.percentile(evac_times, 50)) if evac_times else float("nan"),
        "p90_evac_time": float(np.percentile(evac_times, 90)) if evac_times else float("nan"),
        "max_queue_any_edge": int(max(max_queue_len_per_edge.values())) if max_queue_len_per_edge else 0,
        "bottleneck_events": int(bottleneck_events),
        "avg_queue_load": float(total_queue_time / max(1, cfg.time_limit)),
        "top_bottlenecks": str(bottlenecks),
    }