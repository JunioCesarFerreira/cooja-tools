import json
import re
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

def convert_log_to_csv(log_path: Path, csv_output: Path) -> pd.DataFrame:
    # Regex
    json_pattern = re.compile(r'\[Mote:1\].*?(\{.*?\})')

    # Read and extract JSON
    rows = []

    with log_path.open(encoding="utf-8") as f:
        for line in f:
            m = json_pattern.search(line)
            if not m:
                continue
            try:
                rec = json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
            
            rows.append(rec)

    # DataFrame
    df = pd.DataFrame(rows)
    df.sort_values(["node", "root_time_now"], inplace=True)
    df.to_csv(csv_output, index=False)
    return df


def process_log(log_path: Path, csv_full_output: Path, csv_means_output: Path, dir_plots_output: Path):
    # DataFrame
    df = convert_log_to_csv(log_path, csv_full_output)

    # lost pacckets amount
    df["lost_packets_r2n"] = df["server_sent"] - df["total_received"] 
    df["lost_packets_n2r"] = df["server_sent"] + df["total_sent"] - df["server_received"]

    # Metrics
    metrics_cols = [
        "rtt_latency",
        "r2n_latency",
        "n2r_latency",
        "rssi",
        "radio_rx_energy_mj",
        "radio_tx_energy_mj",
        "cpu_energy_mj",
        "lost_packets_r2n",
        "lost_packets_n2r",
        "hops",
    ]

    means = (
        df.groupby("node")[metrics_cols]
        .mean()
        .round(2)           
        .reset_index()
    )

    means.to_csv(csv_means_output, index=False)
    print("\n=== MEANS PER MOTE ===")
    print(means.to_string(index=False))
    # --------------------------- Plots -----------------------------------------
    unique_nodes = df["node"].unique()

    for metric in metrics_cols:
        plt.figure(figsize=(12, 6))
        for node in unique_nodes:
            node_df = df[df["node"] == node]
            plt.plot(
                node_df["root_time_now"],
                node_df[metric],
                label=f"{node}",
            )
        plt.title(f"{metric} over time")
        plt.xlabel("root_time_now (ms)")
        plt.ylabel(metric)
        plt.legend(loc="upper left", fontsize="small")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        
        safe_metric = re.sub(r"[^A-Za-z0-9_\-]+", "_", metric).strip("_")
        out_path = dir_plots_output / f"{safe_metric}.png"
        plt.savefig(out_path, dpi=150)
        plt.close()