from __future__ import annotations
import pandas as pd

from sim.building import build_apartment_building
from sim.simulation import SimConfig, simulate_one_run
from sim.plots import make_plots

def run_experiment(
    runs: int,
    floors: int,
    apts_per_floor: int,
    stairwells: int,
    occupants_per_apartment: int,
    time_limit: int,
    base_seed: int,
) -> None:
    g, apt_nodes, exit_id = build_apartment_building(
        floors=floors,
        apts_per_floor=apts_per_floor,
        stairwells=stairwells,
    )

    calm_cfg = SimConfig(time_limit=time_limit, panic_enabled=False)
    panic_cfg = SimConfig(time_limit=time_limit, panic_enabled=True)

    rows = []
    for i in range(runs):
        seed = base_seed + i

        calm = simulate_one_run(
            g=g,
            apartment_nodes=apt_nodes,
            exit_id=exit_id,
            cfg=calm_cfg,
            seed=seed,
            occupants_per_apartment=occupants_per_apartment,
        )
        calm["scenario"] = "calm"

        pan = simulate_one_run(
            g=g,
            apartment_nodes=apt_nodes,
            exit_id=exit_id,
            cfg=panic_cfg,
            seed=seed,
            occupants_per_apartment=occupants_per_apartment,
        )
        pan["scenario"] = "panic"

        rows.append(calm)
        rows.append(pan)

    df = pd.DataFrame(rows)
    df.to_csv("results_runs.csv", index=False)

    def summarize(scenario: str) -> dict:
        d = df[df["scenario"] == scenario]
        return {
            "scenario": scenario,
            "runs": int(len(d)),
            "mean_of_mean_evac": float(d["mean_evac_time"].mean()),
            "mean_p90": float(d["p90_evac_time"].mean()),
            "mean_max_queue": float(d["max_queue_any_edge"].mean()),
            "prob_any_not_evacuated": float((d["not_evacuated"] > 0).mean()),
            "mean_bottleneck_events": float(d["bottleneck_events"].mean()),
        }

    summary = pd.DataFrame([summarize("calm"), summarize("panic")])
    summary.to_csv("results_summary.csv", index=False)

    make_plots(df)

    print("Saved:")
    print(" - results_runs.csv")
    print(" - results_summary.csv")
    print(" - figures/evac_time_hist.png")
    print(" - figures/p90_boxplot.png")
    print(" - figures/congestion_boxplot.png")