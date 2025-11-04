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
    
def _last_hextet_decimal(addr: str) -> int:
    addr = addr.split('%', 1)[0]
    ipv6 = ipaddress.IPv6Address(addr)
    hextets = ipv6.exploded.split(':')
    return int(hextets[-1], 16)

def lines_plot(df: pd.DataFrame, cols: list[str], dir_lines: Path):
    unique_nodes = df["node"].unique()

    for metric in cols:
        plt.figure(figsize=(12, 6))
        for node in unique_nodes:
            node_df = df[df["node"] == node]
            if metric not in node_df.columns:
                continue
            plt.plot(
                node_df["root_time_now"],
                node_df[metric],
                marker="o",          # exibe os pontos
                markersize=3,        # tamanho dos marcadores
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
        
def boxes_plot(df: pd.DataFrame, cols: list[str], dir_boxes: Path):
    for metric in cols:
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
            
def bars_plot(df: pd.DataFrame, cols: list[str], dir_bars: Path):
    for metric in cols:
        if metric not in df.columns:
            continue

        safe_metric = re.sub(r"[^A-Za-z0-9_\-]+", "_", metric).strip("_")
        out_path = dir_bars / f"{safe_metric}.png"

        bdf = df[["node", "label", metric]].dropna().copy()
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