from __future__ import annotations
import pandas as pd
import numpy as np
from tqdm import tqdm

from sim.building import build_apartment_building
from sim.simulation import SimConfig, simulate_one_run
from sim.plots import make_plots


def mean_ci(values):
    # Convert to numpy array and remove NaN values
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]

    # Handle small sample sizes
    if len(arr) <= 1:
        return float(np.mean(arr)) if len(arr) > 0 else float("nan"), 0.0

    # Compute mean and 95% confidence interval
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    ci = 1.96 * std / np.sqrt(len(arr))
    return mean, float(ci)


def benchmark_against_reference(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    # Compare calm vs panic results against reference ranges
    for scenario in ["calm", "panic"]:
        d = df[df["scenario"] == scenario]

        reaction_mean_steps = float(d["mean_reaction_time"].mean())
        # Assume 1 simulation step ≈ 1 second for comparison
        reaction_mean_seconds = reaction_mean_steps

        speed_proxy = float(d["mean_speed_mps"].mean())

        rows.append({
            "scenario": scenario,
            "metric": "pre_movement_time_seconds",
            "simulation_mean": reaction_mean_seconds,
            "reference_low": 89.0,
            "reference_high": 220.0,
            "within_reference_band": 89.0 <= reaction_mean_seconds <= 220.0,
            "reference_note": "NIST full-building data discussed pre-evacuation averages around 89 s to 220 s"
        })

        rows.append({
            "scenario": scenario,
            "metric": "stair_speed_mps",
            "simulation_mean": speed_proxy,
            "reference_low": 0.40,
            "reference_high": 0.83,
            "within_reference_band": 0.40 <= speed_proxy <= 0.83,
            "reference_note": "NIST reported observed stair movement speeds around 0.40 to 0.83 m/s in the cited studies"
        })

    return pd.DataFrame(rows)


def run_experiment(
    runs: int,
    floors: int,
    apts_per_floor: int,
    stairwells: int,
    occupants_per_apartment: int,
    time_limit: int,
    base_seed: int,
) -> None:

    # Print configuration being tested
    print(f"\nBuilding configuration: Floors={floors}, Stairs={stairwells}, Occ/Apt={occupants_per_apartment}")
    print(f"Running {runs} Monte Carlo simulations...\n")

    # Build the apartment graph
    g, apt_nodes, exit_id = build_apartment_building(
        floors=floors,
        apts_per_floor=apts_per_floor,
        stairwells=stairwells,
    )

    # Define calm vs panic configurations
    calm_cfg = SimConfig(time_limit=time_limit, panic_enabled=False)
    panic_cfg = SimConfig(time_limit=time_limit, panic_enabled=True)

    rows = []

    # Run Monte Carlo simulations
    for i in tqdm(range(runs), desc="Monte Carlo Runs"):
        seed = base_seed + i  # Ensure reproducibility across runs

        # Run calm scenario
        calm = simulate_one_run(
            g=g,
            apartment_nodes=apt_nodes,
            exit_id=exit_id,
            cfg=calm_cfg,
            seed=seed,
            occupants_per_apartment=occupants_per_apartment,
        )
        calm["scenario"] = "calm"

        # Run panic scenario
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

    # Save raw results for every run
    df = pd.DataFrame(rows)
    df.to_csv("results_runs.csv", index=False)

    def summarize(scenario: str) -> dict:
        # Compute summary statistics for a given scenario
        d = df[df["scenario"] == scenario]

        mean_evac, ci_evac = mean_ci(d["mean_evac_time"])
        mean_total, ci_total = mean_ci(d["mean_total_time_including_failures"])
        mean_p90, ci_p90 = mean_ci(d["p90_evac_time"])
        evac_frac, ci_evac_frac = mean_ci(d["evacuated_fraction"])

        return {
            "scenario": scenario,
            "runs": int(len(d)),
            "mean_of_mean_evac": mean_evac,
            "ci_mean_evac_95": ci_evac,
            "mean_total_time_including_failures": mean_total,
            "ci_total_time_95": ci_total,
            "mean_evacuated_fraction": evac_frac,
            "ci_evacuated_fraction_95": ci_evac_frac,
            "mean_p90": mean_p90,
            "ci_p90_95": ci_p90,
            "mean_max_queue": float(d["max_queue_any_edge"].mean()),
            "prob_any_not_evacuated": float((d["not_evacuated"] > 0).mean()),
            "mean_bottleneck_events": float(d["bottleneck_events"].mean()),
            "mean_floor_clear_time": float(d["max_floor_clear_time"].mean()),
            "mean_panic_freeze_events": float(d["panic_freeze_events"].mean()),
            "mean_panic_bad_route_choices": float(d["panic_bad_route_choices"].mean()),
            "mean_reaction_time": float(d["mean_reaction_time"].mean()),
            "mean_base_speed": float(d["mean_base_speed"].mean()),
        }

    # Build summary table for calm vs panic
    summary = pd.DataFrame([summarize("calm"), summarize("panic")])

    calm_row = summary[summary["scenario"] == "calm"].iloc[0]
    panic_row = summary[summary["scenario"] == "panic"].iloc[0]

    # Compute differences between scenarios
    comparison = {
        "difference_panic_minus_calm_mean_evac": float(panic_row["mean_of_mean_evac"] - calm_row["mean_of_mean_evac"]),
        "difference_panic_minus_calm_total_time": float(panic_row["mean_total_time_including_failures"] - calm_row["mean_total_time_including_failures"]),
        "difference_panic_minus_calm_evacuated_fraction": float(panic_row["mean_evacuated_fraction"] - calm_row["mean_evacuated_fraction"]),
        "difference_panic_minus_calm_max_queue": float(panic_row["mean_max_queue"] - calm_row["mean_max_queue"]),
    }

    for k, v in comparison.items():
        summary[k] = v

    # Save summary results
    summary.to_csv("results_summary.csv", index=False)

    # Benchmark against reference values
    benchmark = benchmark_against_reference(df)
    benchmark.to_csv("benchmark_comparison.csv", index=False)

    # Generate plots
    make_plots(df)

    print("\nSimulation complete.")
    print("Saved:")
    print(" - results_runs.csv")
    print(" - results_summary.csv")
    print(" - benchmark_comparison.csv")
    print(" - figures/evac_time_hist.png")
    print(" - figures/p90_boxplot.png")
    print(" - figures/congestion_boxplot.png")
    print(" - figures/evacuated_fraction_boxplot.png")
    print(" - figures/penalized_total_time_boxplot.png")


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

    # Loop through all combinations of parameters
    for floors in floor_list:
        for stairs in stair_list:
            for occ in occ_list:
                print("\n======================================")
                print(f"Running config: Floors={floors}, Stairs={stairs}, Occ/Apt={occ}")
                print("======================================")

                # Run experiment for current configuration
                run_experiment(
                    runs=runs,
                    floors=floors,
                    apts_per_floor=apts_per_floor,
                    stairwells=stairs,
                    occupants_per_apartment=occ,
                    time_limit=time_limit,
                    base_seed=base_seed,
                )

                # Load summary and tag with configuration
                df = pd.read_csv("results_summary.csv")
                df["floors"] = floors
                df["stairs"] = stairs
                df["occupancy"] = occ
                all_results.append(df)

    # Combine all configurations into one file
    final_df = pd.concat(all_results, ignore_index=True)
    final_df.to_csv("experiment_matrix_summary.csv", index=False)

    print("\nMatrix experiment complete.")
    print("Saved: experiment_matrix_summary.csv")
