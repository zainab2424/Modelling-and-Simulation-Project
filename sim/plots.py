from __future__ import annotations
import os
import matplotlib.pyplot as plt
import pandas as pd

def make_plots(df: pd.DataFrame, out_dir: str = "figures") -> None:
    os.makedirs(out_dir, exist_ok=True)

    # Histogram of mean evac time per run
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

    # p90 boxplot
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

    # congestion boxplot
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