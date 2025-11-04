import json
import re
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from library.plots import lines_plot, boxes_plot, bars_plot
from library.throughput import throughput_compute_and_plot

# Try to use seaborn for boxplots; fall back to matplotlib if not available
try:
    import seaborn as sns  # type: ignore
except Exception:  # seaborn not installed
    sns = None

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
    # Ensure the presence of important columns even if missing
    if "node" not in df.columns:
        df["node"] = "unknown"
    if "root_time_now" not in df.columns:
        df["root_time_now"] = range(len(df))

    df.sort_values(["node", "root_time_now"], inplace=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_output, index=False)
    return df

def process_log(
    log_path: Path,
    csv_full_output: Path,
    csv_means_output: Path,
    dir_plots_output: Path
):
    # DataFrame
    df = convert_log_to_csv(log_path, csv_full_output)

    # Lost packet count (create only if the base columns exist)
    if {"server_sent", "total_received"}.issubset(df.columns):
        df["lost_packets_r2n"] = df["server_sent"] - df["total_received"]
    else:
        df["lost_packets_r2n"] = pd.NA

    if {"server_sent", "total_sent", "server_received"}.issubset(df.columns):
        df["lost_packets_n2r"] = df["server_sent"] + df["total_sent"] - df["server_received"]
    else:
        df["lost_packets_n2r"] = pd.NA

    # Metrics (filter only the ones that exist in the DataFrame)
    desired_metrics = [
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
    metrics_cols = [c for c in desired_metrics if c in df.columns]
    
    dir_plots_output.mkdir(parents=True, exist_ok=True)
    dir_lines = dir_plots_output / "lines"
    dir_boxes = dir_plots_output / "boxes"
    dir_bars  = dir_plots_output / "bars"
    dir_lines.mkdir(exist_ok=True)
    dir_boxes.mkdir(exist_ok=True)
    dir_bars.mkdir(exist_ok=True)

    # LINES chart
    lines_plot(df, metrics_cols, dir_lines)
    
    # Map numeric label 2,3,... per node (also used in plots)
    node_order = sorted(df["node"].astype(str).unique())
    node_to_labelnum = {n: i + 2 for i, n in enumerate(node_order)}
    df["label"] = df["node"].astype(str).map(node_to_labelnum)

    # BOXES chart
    boxes_plot(df, metrics_cols, dir_boxes)
     
    # Means per node
    if metrics_cols:
        means_df = (
            df.groupby("node")[metrics_cols]
            .mean(numeric_only=True)
            .round(3)
            .reset_index()
        )
    else:
        means_df = pd.DataFrame(columns=["node"])

    # Add numeric label (2,3,...) to means CSV
    means_df["label"] = means_df["node"].astype(str).map(node_to_labelnum)

    csv_means_output.parent.mkdir(parents=True, exist_ok=True)
    means_df.to_csv(csv_means_output, index=False)

    print("\n=== MEANS PER MOTE ===")
    if not means_df.empty:
        print(means_df.to_string(index=False))
    else:
        print("(no metrics found to compute means)")

    # BARS chart
    if not means_df.empty:
        bars_plot(means_df, metrics_cols, dir_bars)
            
            
    for c in ["server_sent", "server_received"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")            
            
    # ---------- Grouped bar chart: 4 bars per node (max in raw data) ----------
    raw_cols = [c for c in ["server_sent", "server_received", "total_sent", "total_received"] if c in df.columns]
    if raw_cols:
        max_df = (
            df.groupby("node")[raw_cols]
              .max(numeric_only=True)
              .rename(columns={
                  "server_sent":     "server_sent_max",
                  "server_received": "server_received_max",
                  "total_sent":      "total_sent_max",
                  "total_received":  "total_received_max"
              })
              .reset_index()
        )

        # Map numeric labels 2,3,... in the same order
        node_order = sorted(df["node"].astype(str).unique())
        node_to_labelnum = {n: i + 2 for i, n in enumerate(node_order)}
        max_df["label"] = max_df["node"].astype(str).map(node_to_labelnum)
        max_df = max_df.sort_values("label")

        # Keep only columns that actually exist
        value_vars = [c for c in ["server_sent_max", "server_received_max", "total_sent_max", "total_received_max"] if c in max_df.columns]

        out_path = dir_bars / "counters_max_grouped.png"

        if sns is not None:
            # --- using seaborn (simpler) ---
            plot_df = max_df.melt(
                id_vars=["node", "label"],
                value_vars=value_vars,
                var_name="kind",
                value_name="value"
            )
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.barplot(data=plot_df, x="label", y="value", hue="kind", ax=ax)

            ax.set_title("Counters (max per node in raw data) — grouped")
            ax.set_xlabel("Node (numeric label starting from 2)")
            ax.set_ylabel("count (max)")
            ax.grid(True, linestyle="--", alpha=0.5, axis="y")
            fig.tight_layout()
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
        else:
            # --- matplotlib fallback: manually grouped bars ---
            import numpy as np  # local import to avoid changing the file's top imports

            x = np.arange(len(max_df))  # one position per node
            K = len(value_vars)
            total_width = 0.8
            width = total_width / max(1, K)
            offsets = (np.arange(K) - (K - 1) / 2) * width

            fig, ax = plt.subplots(figsize=(12, 6))
            for i, col in enumerate(value_vars):
                ax.bar(
                    x + offsets[i],
                    max_df[col].values,
                    width=width,
                    label=col
                )

            ax.set_xticks(x)
            ax.set_xticklabels(max_df["label"].astype(str).tolist())
            ax.set_title("Counters (max per node in raw data) — grouped")
            ax.set_xlabel("Node (numeric label starting from 2)")
            ax.set_ylabel("count (max)")
            ax.legend(title="kind", fontsize="small")
            ax.grid(True, linestyle="--", alpha=0.5, axis="y")
            fig.tight_layout()
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
   
    throughput_compute_and_plot(df, csv_means_output, dir_lines, dir_boxes)
