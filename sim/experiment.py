from __future__ import annotations
import pandas as pd
import numpy as np
from tqdm import tqdm

from sim.building import build_apartment_building
from sim.simulation import SimConfig, simulate_one_run
from sim.plots import make_plots


def mean_ci(values):
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) <= 1:
        return float(np.mean(arr)) if len(arr) > 0 else float("nan"), 0.0
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    ci = 1.96 * std / np.sqrt(len(arr))
    return mean, float(ci)


def run_experiment(
    runs: int,
    floors: int,
    apts_per_floor: int,
    stairwells: int,
    occupants_per_apartment: int,
    time_limit: int,
    base_seed: int,
) -> None:

    print(f"\nBuilding configuration: Floors={floors}, Stairs={stairwells}, Occ/Apt={occupants_per_apartment}")
    print(f"Running {runs} Monte Carlo simulations...\n")

    g, apt_nodes, exit_id = build_apartment_building(
        floors=floors,
        apts_per_floor=apts_per_floor,
        stairwells=stairwells,
    )

    calm_cfg = SimConfig(time_limit=time_limit, panic_enabled=False)
    panic_cfg = SimConfig(time_limit=time_limit, panic_enabled=True)

    rows = []

    for i in range(runs):

       for i in tqdm(range(runs), desc="Monte Carlo Runs"):

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

    # -------------------------
    # Statistical Summary
    # -------------------------

    def summarize(scenario: str) -> dict:
        d = df[df["scenario"] == scenario]

        mean_evac, ci_evac = mean_ci(d["mean_evac_time"])
        mean_p90, ci_p90 = mean_ci(d["p90_evac_time"])

        return {
            "scenario": scenario,
            "runs": int(len(d)),
            "mean_of_mean_evac": mean_evac,
            "ci_mean_evac_95": ci_evac,
            "mean_p90": mean_p90,
            "ci_p90_95": ci_p90,
            "mean_max_queue": float(d["max_queue_any_edge"].mean()),
            "prob_any_not_evacuated": float((d["not_evacuated"] > 0).mean()),
            "mean_bottleneck_events": float(d["bottleneck_events"].mean()),
            "mean_floor_clear_time": float(d["max_floor_clear_time"].mean()),
        }

    summary = pd.DataFrame([summarize("calm"), summarize("panic")])

    # ---- Add statistical difference
    calm_mean = summary.loc[summary["scenario"] == "calm", "mean_of_mean_evac"].values[0]
    panic_mean = summary.loc[summary["scenario"] == "panic", "mean_of_mean_evac"].values[0]

    summary["difference_panic_minus_calm"] = panic_mean - calm_mean

    summary.to_csv("results_summary.csv", index=False)

    # -------------------------
    # Plots
    # -------------------------
    make_plots(df)

    print("\nSimulation complete.")
    print("Saved:")
    print(" - results_runs.csv")
    print(" - results_summary.csv")
    print(" - figures/evac_time_hist.png")
    print(" - figures/p90_boxplot.png")
    print(" - figures/congestion_boxplot.png")


# ====================================================
# OPTIONAL: Structured Experiment Matrix
# ====================================================

def run_experiment_matrix(
    runs: int,
    floor_list: list[int],
    stair_list: list[int],
    occ_list: list[int],
    time_limit: int,
    base_seed: int,
    apts_per_floor: int = 10,
) -> None:

    all_results = []

    for floors in floor_list:
        for stairs in stair_list:
            for occ in occ_list:

                print("\n======================================")
                print(f"Running config: Floors={floors}, Stairs={stairs}, Occ/Apt={occ}")
                print("======================================")

                run_experiment(
                    runs=runs,
                    floors=floors,
                    apts_per_floor=apts_per_floor,
                    stairwells=stairs,
                    occupants_per_apartment=occ,
                    time_limit=time_limit,
                    base_seed=base_seed,
                )

                df = pd.read_csv("results_summary.csv")
                df["floors"] = floors
                df["stairs"] = stairs
                df["occupancy"] = occ
                all_results.append(df)

    final_df = pd.concat(all_results, ignore_index=True)
    final_df.to_csv("experiment_matrix_summary.csv", index=False)

    print("\nMatrix experiment complete.")
    print("Saved: experiment_matrix_summary.csv")