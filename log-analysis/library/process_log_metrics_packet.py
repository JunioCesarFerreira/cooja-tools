import json
import re
import pandas as pd
import ipaddress
from pathlib import Path
import matplotlib.pyplot as plt

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

def _last_hextet_decimal(addr: str) -> int:
    addr = addr.split('%', 1)[0]
    ipv6 = ipaddress.IPv6Address(addr)
    hextets = ipv6.exploded.split(':')
    return int(hextets[-1], 16)

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

    # --------------------------- Line plots --------------------------------
    dir_plots_output.mkdir(parents=True, exist_ok=True)
    dir_lines = dir_plots_output / "lines"
    dir_boxes = dir_plots_output / "boxes"
    dir_bars  = dir_plots_output / "bars"
    dir_lines.mkdir(exist_ok=True)
    dir_boxes.mkdir(exist_ok=True)
    dir_bars.mkdir(exist_ok=True)

    unique_nodes = df["node"].unique()

    for metric in metrics_cols:
        plt.figure(figsize=(12, 6))
        for node in unique_nodes:
            node_df = df[df["node"] == node]
            if metric not in node_df.columns:
                continue
            plt.plot(
                node_df["root_time_now"],
                node_df[metric],
                label=f"{_last_hextet_decimal(node)}",
            )
        plt.title(f"{metric} over time")
        plt.xlabel("root_time_now (ms)")
        plt.ylabel(metric)

        # Legend outside the chart (to the right)
        plt.legend(
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize="small",
            frameon=False
        )

        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()

        safe_metric = re.sub(r"[^A-Za-z0-9_\-]+", "_", metric).strip("_")
        out_path = dir_lines / f"{safe_metric}.png"
        plt.savefig(out_path, dpi=150)
        plt.close()

    # --------------------------- CSV of means  ------------------------------
    # Map numeric label 2,3,... per node (also used in plots)
    node_order = sorted(df["node"].astype(str).unique())
    node_to_labelnum = {n: i + 2 for i, n in enumerate(node_order)}
    df["label"] = df["node"].astype(str).map(node_to_labelnum)

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

    # --------------------------- Boxplots --------------------------------------
    for metric in metrics_cols:
        safe_metric = re.sub(r"[^A-Za-z0-9_\-]+", "_", metric).strip("_")
        out_path = dir_boxes / f"{safe_metric}.png"

        fdf = df.dropna(subset=[metric])
        if fdf.empty:
            continue

        if sns is not None:
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.boxplot(
                data=fdf,
                x="label", y=metric, hue="node",
                ax=ax, showcaps=True, width=0.6
            )
            # Remove legend
            if ax.get_legend():
                ax.get_legend().remove()
            ax.set_title(metric)
            ax.set_xlabel("")
            ax.set_ylabel(metric)
            ax.grid(True, linestyle="--", alpha=0.5)
            sns.despine(ax=ax)
            fig.tight_layout()
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
        else:
            # Fallback
            fdf = fdf.copy()
            fdf["_cat"] = fdf["label"].astype(str) + " | " + fdf["node"].astype(str)
            cats = list(fdf["_cat"].unique())
            data = [fdf.loc[fdf["_cat"] == c, metric].dropna().values for c in cats]

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.boxplot(data, patch_artist=True, widths=0.6, showcaps=True)
            ax.set_xticks(range(1, len(cats) + 1))
            ax.set_xticklabels(cats, rotation=20, ha="right")
            ax.set_title(f"{metric} (non-seaborn)")
            ax.set_xlabel("")
            ax.set_ylabel(metric)
            ax.grid(True, linestyle="--", alpha=0.5)
            fig.tight_layout()
            fig.savefig(out_path, dpi=150)
            plt.close(fig)

    # --------------------------- Bar charts (means) -------------------------------
    # For each metric, plot bars showing the mean per node (X-axis = label 2,3,...)
    if not means_df.empty:
        # Prepare table (node, label, mean_value) for each metric
        for metric in metrics_cols:
            if metric not in means_df.columns:
                continue

            safe_metric = re.sub(r"[^A-Za-z0-9_\-]+", "_", metric).strip("_")
            out_path = dir_bars / f"{safe_metric}.png"

            bdf = means_df[["node", "label", metric]].dropna().copy()
            # Sort by label (numeric)
            bdf = bdf.sort_values("label")

            fig, ax = plt.subplots(figsize=(10, 5))
            if sns is not None:
                sns.barplot(data=bdf, x="label", y=metric, ax=ax)
            else:
                ax.bar(bdf["label"].astype(str).values, bdf[metric].values)

            ax.set_title(f"{metric} (mean per node)")
            ax.set_xlabel("Node (numeric label starting from 2)")
            ax.set_ylabel(metric)
            ax.grid(True, linestyle="--", alpha=0.5, axis="y")
            fig.tight_layout()
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            
    for c in ["server_sent", "server_received"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    # ---------- Bar charts (accumulated per node via MAX from raw data) ----------
    # server_sent_max and server_received_max
    raw_cols = [c for c in ["server_sent", "server_received"] if c in df.columns]
    if raw_cols:
        max_df = (
            df.groupby("node")[raw_cols]
              .max(numeric_only=True)
              .rename(columns={
                  "server_sent": "server_sent_max",
                  "server_received": "server_received_max"
              })
              .reset_index()
        )
        # Map label 2,3,... to maintain the same visual order
        node_order = sorted(df["node"].astype(str).unique())
        node_to_labelnum = {n: i + 2 for i, n in enumerate(node_order)}
        max_df["label"] = max_df["node"].astype(str).map(node_to_labelnum)
        max_df = max_df.sort_values("label")

        for col in ["server_sent_max", "server_received_max"]:
            if col not in max_df.columns:
                continue

            safe_name = re.sub(r"[^A-Za-z0-9_\-]+", "_", col).strip("_")
            out_path = (dir_bars / f"{safe_name}.png")

            fig, ax = plt.subplots(figsize=(10, 5))
            if sns is not None:
                sns.barplot(data=max_df, x="label", y=col, ax=ax)
            else:
                ax.bar(max_df["label"].astype(str).values, max_df[col].values)

            # Titles/labels
            ax.set_title(f"{col} (maximum observed per node in raw data)")
            ax.set_xlabel("Node (numeric label starting from 2)")
            ax.set_ylabel(col)
            ax.grid(True, linestyle="--", alpha=0.5, axis="y")
            fig.tight_layout()
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
