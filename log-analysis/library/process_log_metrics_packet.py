import json
import re
import pandas as pd
import ipaddress
from pathlib import Path
import matplotlib.pyplot as plt

# tenta usar seaborn para os boxplots; faz fallback para matplotlib se não houver
try:
    import seaborn as sns  # type: ignore
except Exception:  # seaborn não instalado
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
    # garante presença de colunas importantes mesmo se faltarem
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

    # lost packets amount (só cria se as colunas base existirem)
    if {"server_sent", "total_received"}.issubset(df.columns):
        df["lost_packets_r2n"] = df["server_sent"] - df["total_received"]
    else:
        df["lost_packets_r2n"] = pd.NA

    if {"server_sent", "total_sent", "server_received"}.issubset(df.columns):
        df["lost_packets_n2r"] = df["server_sent"] + df["total_sent"] - df["server_received"]
    else:
        df["lost_packets_n2r"] = pd.NA

    # Métricas (filtra apenas as que existem no DF)
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

    # Means por mote
    if metrics_cols:
        means = (
            df.groupby("node")[metrics_cols]
            .mean(numeric_only=True)
            .round(2)
            .reset_index()
        )
    else:
        means = pd.DataFrame(columns=["node"])
    csv_means_output.parent.mkdir(parents=True, exist_ok=True)
    means.to_csv(csv_means_output, index=False)

    print("\n=== MEANS PER MOTE ===")
    if not means.empty:
        print(means.to_string(index=False))
    else:
        print("(nenhuma métrica encontrada para calcular médias)")

    # --------------------------- Plots -----------------------------------------
    dir_plots_output.mkdir(parents=True, exist_ok=True)
    dir_lines = dir_plots_output / "lines"
    dir_boxes = dir_plots_output / "boxes"
    dir_lines.mkdir(exist_ok=True)
    dir_boxes.mkdir(exist_ok=True)

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

    node_order = sorted(df["node"].astype(str).unique())
    node_to_labelnum = {n: i + 2 for i, n in enumerate(node_order)}
    df["label"] = df["node"].astype(str).map(node_to_labelnum)

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
            bp = ax.boxplot(data, patch_artist=True, widths=0.6, showcaps=True)
            ax.set_xticks(range(1, len(cats) + 1))
            ax.set_xticklabels(cats, rotation=20, ha="right")
            ax.set_title(f"{metric} (non seaborn)")
            ax.set_xlabel("")
            ax.set_ylabel(metric)
            ax.grid(True, linestyle="--", alpha=0.5)
            fig.tight_layout()
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
