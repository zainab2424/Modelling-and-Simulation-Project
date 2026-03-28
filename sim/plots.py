
from __future__ import annotations
import os
import matplotlib.pyplot as plt
import pandas as pd


def make_plots(df: pd.DataFrame, out_dir: str = "figures") -> None:
    os.makedirs(out_dir, exist_ok=True)

    plt.figure()
    for scen in ["calm", "panic"]:
        d = df[df["scenario"] == scen]["mean_evac_time"].dropna().values
        plt.hist(d, bins=20, alpha=0.6, label=scen)
    plt.xlabel("Mean evacuation time (steps)")
    plt.ylabel("Count")
    plt.title("Distribution of mean evacuation time per run")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "evac_time_hist.png"))
    plt.close()

    plt.figure()
    data = [
        df[df["scenario"] == "calm"]["p90_evac_time"].dropna().values,
        df[df["scenario"] == "panic"]["p90_evac_time"].dropna().values,
    ]
    plt.boxplot(data, labels=["calm", "panic"])
    plt.ylabel("p90 evacuation time (steps)")
    plt.title("p90 evacuation time: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "p90_boxplot.png"))
    plt.close()

    plt.figure()
    data2 = [
        df[df["scenario"] == "calm"]["max_queue_any_edge"].values,
        df[df["scenario"] == "panic"]["max_queue_any_edge"].values,
    ]
    plt.boxplot(data2, labels=["calm", "panic"])
    plt.ylabel("Max queue length on any edge")
    plt.title("Worst congestion: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "congestion_boxplot.png"))
    plt.close()

    plt.figure()
    data3 = [
        df[df["scenario"] == "calm"]["evacuated_fraction"].values,
        df[df["scenario"] == "panic"]["evacuated_fraction"].values,
    ]
    plt.boxplot(data3, labels=["calm", "panic"])
    plt.ylabel("Evacuated fraction")
    plt.title("Evacuation success rate: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "evacuated_fraction_boxplot.png"))
    plt.close()

    plt.figure()
    data4 = [
        df[df["scenario"] == "calm"]["mean_total_time_including_failures"].values,
        df[df["scenario"] == "panic"]["mean_total_time_including_failures"].values,
    ]
    plt.boxplot(data4, labels=["calm", "panic"])
    plt.ylabel("Mean total time incl. failures (steps)")
    plt.title("Overall evacuation burden: calm vs panic")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "penalized_total_time_boxplot.png"))
    plt.close()
