from __future__ import annotations
import os
import matplotlib.pyplot as plt
import pandas as pd


def make_plots(df: pd.DataFrame, out_dir: str = "figures") -> None:
    # Ensure the output directory exists (creates it if missing)
    os.makedirs(out_dir, exist_ok=True)

    # =========================================
    # Histogram of mean evacuation time per run
    # =========================================
    plt.figure()
    for scen in ["calm", "panic"]:
        # Filter data for each scenario and remove NaN values
        d = df[df["scenario"] == scen]["mean_evac_time"].dropna().values
        plt.hist(d, bins=20, alpha=0.6, label=scen)  # Overlay both scenarios
    plt.xlabel("Mean evacuation time (steps)")
    plt.ylabel("Count")
    plt.title("Distribution of mean evacuation time per run")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "evac_time_hist.png"))
    plt.close()

    # =========================================
    # Boxplot of p90 evacuation time
    # =========================================
    plt.figure()
    data = [
        df[df["scenario"] == "calm"]["p90_evac_time"].dropna().values,
        df[df["scenario"] == "panic"]["p90_evac_time"].dropna().values,
    ]
    # Compare worst-case evacuation times between scenarios
    plt.boxplot(data, labels=["calm", "panic"])
    plt.ylabel("p90 evacuation time (steps)")
    plt.title("p90 evacuation time: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "p90_boxplot.png"))
    plt.close()

    # =========================================
    # Boxplot of maximum congestion (queue size)
    # =========================================
    plt.figure()
    data2 = [
        df[df["scenario"] == "calm"]["max_queue_any_edge"].values,
        df[df["scenario"] == "panic"]["max_queue_any_edge"].values,
    ]
    # Shows how severe bottlenecks get in each scenario
    plt.boxplot(data2, labels=["calm", "panic"])
    plt.ylabel("Max queue length on any edge")
    plt.title("Worst congestion: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "congestion_boxplot.png"))
    plt.close()

    # =========================================
    # Boxplot of evacuation success rate
    # =========================================
    plt.figure()
    data3 = [
        df[df["scenario"] == "calm"]["evacuated_fraction"].values,
        df[df["scenario"] == "panic"]["evacuated_fraction"].values,
    ]
    # Higher values indicate more successful evacuations
    plt.boxplot(data3, labels=["calm", "panic"])
    plt.ylabel("Evacuated fraction")
    plt.title("Evacuation success rate: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "evacuated_fraction_boxplot.png"))
    plt.close()

    # =========================================
    # Boxplot of total evacuation time (including failures)
    # =========================================
    plt.figure()
    data4 = [
        df[df["scenario"] == "calm"]["mean_total_time_including_failures"].values,
        df[df["scenario"] == "panic"]["mean_total_time_including_failures"].values,
    ]
    # Penalizes runs where agents did not evacuate (uses time_limit)
    plt.boxplot(data4, labels=["calm", "panic"])
    plt.ylabel("Mean total time incl. failures (steps)")
    plt.title("Overall evacuation burden: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "penalized_total_time_boxplot.png"))
    plt.close()
