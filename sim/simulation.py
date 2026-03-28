# sim/simulation.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import random
import numpy as np
import math

from sim.building import BuildingGraph
from sim.agents import Agent, create_agents
from sim.hazard import FireHazard
from sim.routing import edge_between, compute_distances_to_goal

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

@dataclass
class SimConfig:
    time_limit: int = 600
    reaction_logn_mu: float = 4.2
    reaction_logn_sigma: float = 0.6
    susceptibility_alpha: float = 2.0
    susceptibility_beta: float = 2.5
    speed_mean: float = 1.0
    speed_std: float = 0.10

    panic_enabled: bool = True
    # INCREASED: Weights for a more noticeable impact
    panic_from_hazard_weight: float = 0.95 
    panic_from_neighbors_weight: float = 0.85 
    panic_decay: float = 0.01 
    panic_threshold_move_change: float = 0.25

    slowdown_per_danger: float = 2.5
    block_prob_when_high: float = 0.15

def simulate_one_run(
    g: BuildingGraph,
    apartment_nodes: List[int],
    exit_id: int,
    cfg: SimConfig,
    seed: int,
    occupants_per_apartment: int = 2,
    ignition_floor: Optional[int] = None,
) -> Dict:

    np_rng = np.random.default_rng(seed)
    rng = random.Random(seed)

    agents = create_agents(
        apartment_nodes=apartment_nodes,
        occupants_per_apartment=occupants_per_apartment,
        reaction_logn_mu=cfg.reaction_logn_mu,
        reaction_logn_sigma=cfg.reaction_logn_sigma,
        susceptibility_alpha=cfg.susceptibility_alpha,
        susceptibility_beta=cfg.susceptibility_beta,
        speed_mean=cfg.speed_mean,
        speed_std=cfg.speed_std,
        rng=rng,
        np_rng=np_rng
    )

    max_floor = max(g.floor_of_node.values())
    if ignition_floor is None:
        ignition_floor = rng.randint(1, max_floor)

    corridor_candidates = [
        n for n, t in g.node_types.items()
        if t == "corr" and g.floor_of_node[n] == ignition_floor
    ]
    ignition_node = rng.choice(corridor_candidates)
    hazard = FireHazard(ignition_node=ignition_node)
    hazard.initialize()

    edge_queues: Dict[int, List[int]] = {i: [] for i in range(len(g.edges))}
    max_queue_len_per_edge: Dict[int, int] = {i: 0 for i in range(len(g.edges))}
    
    total_queue_time = 0
    bottleneck_events = 0
    panic_freeze_events = 0
    panic_bad_route_choices = 0
    floor_clear_time: Dict[int, int] = {}
    stair_usage: Dict[int, int] = {}
    dynamic_blocked_edges: Set[int] = set()
    total_distance_traveled = 0.0
    total_time_traveled = 0

    # ================= MAIN LOOP =================
    for t in range(cfg.time_limit):
        # 1. Handle agents currently moving
        for a in agents:
            if a.status == "moving":
                # Panic-driven hesitation (freezing in place mid-hallway)
                if cfg.panic_enabled and a.panic > 0.25:
                    if rng.random() < (0.7 * a.panic): # Adjusted for balance
                        panic_freeze_events += 1
                        continue

                a.remaining_travel -= 1
                if a.remaining_travel <= 0:
                    a.node = a.moving_to
                    a.status = "waiting"
                    a.moving_to = None
                    a.moving_edge_idx = None
        
        hazard.step(g, rng)
        
        # 2. Panic contagion (Social Spread)
        if cfg.panic_enabled:
            node_occupancy = {}
            for a in agents:
                if a.status != "evacuated":
                    node_occupancy.setdefault(a.node, []).append(a)

            for node_id, group in node_occupancy.items():
                panicked_count = sum(1 for a in group if a.panic > 0.6)
                danger_here = hazard.danger.get(node_id, 0.0)
                
                for a in group:
                    # Combined growth from hazard and neighbors
                    increase = (danger_here * cfg.panic_from_hazard_weight) + \
                               (0.15 * panicked_count * cfg.panic_from_neighbors_weight)
                    a.panic = clamp01(a.panic + (increase * a.panic_susceptibility * 0.1))

        # 3. Dynamic Edge Updates
        dynamic_blocked_edges.clear()
        for eidx, e in enumerate(g.edges):
            danger = max(hazard.danger.get(e.src, 0.0), hazard.danger.get(e.dst, 0.0))
            e.slowdown = 1.0 + danger * cfg.slowdown_per_danger
            
            if danger >= hazard.block_threshold and rng.random() < cfg.block_prob_when_high:
                e.blocked = True
            if danger < 0.35 and e.blocked and rng.random() < 0.15:
                e.blocked = False
            
            if e.blocked:
                dynamic_blocked_edges.add(eidx)

        dist_to_exit = compute_distances_to_goal(g, exit_id, dynamic_blocked_edges)

        # 4. Movement Decisions
        for a in agents:
            if a.status in ("evacuated", "stuck") or t < a.reaction_time:
                continue
            
            # Initial exit check
            if a.node == exit_id:
                a.status = "evacuated"
                a.evac_time = t
                continue

            # Panic Freezing (at the node)
            if cfg.panic_enabled and a.panic > 0.6:
                if rng.random() < (0.3 * a.panic):
                    panic_freeze_events += 1
                    continue

            if a.node not in dist_to_exit:
                continue

            # Pathfinding
            candidates = []
            for nb in g.neighbors(a.node):
                eidx_check = edge_between(g, a.node, nb)
                if eidx_check is not None and eidx_check not in dynamic_blocked_edges:
                    if nb in dist_to_exit:
                        candidates.append((dist_to_exit[nb], nb))

            if not candidates:
                continue

            candidates.sort(key=lambda x: x[0])
            next_hop = candidates[0][1]
            
            # Irrational routing
            if cfg.panic_enabled and a.panic > 0.3:
                # 20% max chance to make a mistake when fully panicked (panic=1.0)
                mistake_probability = 0.70 * a.panic 
                
                if rng.random() < mistake_probability:
                    # Pick any neighbor at random (could be a wrong turn!)
                    all_neighbors = list(g.neighbors(a.node))
                    if all_neighbors:
                        next_hop = rng.choice(all_neighbors)
                        # Only count it as a "bad route" if they didn't accidentally pick the right one
                        if next_hop != candidates[0][1]:
                            panic_bad_route_choices += 1
            # --- UPDATED IRRATIONAL ROUTING END ---
            eidx_final = edge_between(g, a.node, next_hop)
            if eidx_final is not None and a.agent_id not in edge_queues[eidx_final]:
                edge_queues[eidx_final].append(a.agent_id)

        # 5. Process Queues (The Crush Mechanic)
        for eidx, q in edge_queues.items():
            if not q: continue
            
            e = g.edges[eidx]
            cap = e.effective_capacity()
            
            if cfg.panic_enabled:
                panic_ratio = sum(1 for aid in q if agents[aid].panic > 0.6) / len(q)
                if panic_ratio >= 0.1:
                    # AGGRESSIVE COLLAPSE: math.floor makes reductions stickier
                    cap = max(0, math.floor(cap * (1.0 - 0.95 * panic_ratio)))

            max_queue_len_per_edge[eidx] = max(max_queue_len_per_edge[eidx], len(q))
            if len(q) >= 10: bottleneck_events += 1

            to_move = q[:cap]
            edge_queues[eidx] = q[cap:]

            for aid in to_move:
                ag = agents[aid]
                if ag.status == "waiting":
                    eff_speed = ag.base_speed
                    if cfg.panic_enabled and ag.panic > 0.4:
                        eff_speed *= (0.75 - 0.6 * ag.panic) # Panicked speed reduction

                    travel = max(1, int(round(e.distance_m / max(0.2, eff_speed))))
                    ag.status = "moving"
                    ag.remaining_travel = travel
                    ag.moving_to = e.dst
                    
                    total_distance_traveled += e.distance_m
                    total_time_traveled += travel
                    if g.node_types.get(e.dst) == "stair":
                        stair_usage[e.dst] = stair_usage.get(e.dst, 0) + 1

            total_queue_time += len(edge_queues[eidx])

        # 6. Floor Clearance Tracking
        remaining_floors = {g.floor_of_node[a.node] for a in agents if a.status != "evacuated" and a.node in g.floor_of_node}
        for f in range(1, max_floor + 1):
            if f not in remaining_floors and f not in floor_clear_time:
                floor_clear_time[f] = t

        if all(a.status == "evacuated" for a in agents):
            break

    # Results calculation logic
    evac_times = [a.evac_time for a in agents if a.evac_time is not None]
    not_evacuated = sum(1 for a in agents if a.status != "evacuated")
    
    return {
        "seed": seed,
        "agents": len(agents),
        "evacuated": len(evac_times),
        "not_evacuated": not_evacuated,
        "mean_evac_time": float(np.mean(evac_times)) if evac_times else float("nan"),
        "p90_evac_time": float(np.percentile(evac_times, 90)) if evac_times else float("nan"),
        "max_queue_any_edge": int(max(max_queue_len_per_edge.values())),
        "bottleneck_events": int(bottleneck_events),
        "avg_queue_load": float(total_queue_time / max(1, cfg.time_limit)),
        "mean_speed_mps": total_distance_traveled / total_time_traveled if total_time_traveled > 0 else 0.0,
        "mean_total_time_including_failures": float(np.mean([a.evac_time if a.evac_time else cfg.time_limit for a in agents])),
        "evacuated_fraction": len(evac_times) / len(agents) if agents else 0.0,
        "max_floor_clear_time": max(floor_clear_time.values()) if floor_clear_time else cfg.time_limit,
        "panic_freeze_events": panic_freeze_events,
        "panic_bad_route_choices": panic_bad_route_choices,
        "mean_reaction_time": float(np.mean([a.reaction_time for a in agents])),
        "mean_base_speed": float(np.mean([a.base_speed for a in agents]))
    }