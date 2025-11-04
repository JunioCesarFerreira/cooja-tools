import re
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from library.plots import _last_hextet_decimal

# Try to use seaborn for boxplots; fall back to matplotlib if not available
try:
    import seaborn as sns  # type: ignore
except Exception:  # seaborn not installed
    sns = None

def _compute_throughput_per_interval(
    df: pd.DataFrame,
    count_col: str,
    interval_ms: int = 1000
) -> pd.DataFrame:
    """
    Computes throughput (pkts/s) per 'node' in fixed windows.
    Assumes 'count_col' is a cumulative, non-decreasing counter.
    Strategy:
      1) For each node: sort by time and compute diffs (increments >= 0).
      2) Assign each increment to the bin of the "later" sample (where the count+delta occurs).
      3) Aggregate by summing increments per (node, bin).
      4) Rate = sum_increments / (interval_ms/1000). We use a fixed dt for all bins.
    Returns columns: ['node', 'bin', 'bin_start_ms', 'bin_end_ms', 'rate_pkts_per_s', 'kind']
    """
    if count_col not in df.columns:
        return pd.DataFrame(columns=["node", "bin", "bin_start_ms", "bin_end_ms", "rate_pkts_per_s", "kind"])

    # filter only rows with a valid counter
    sub = df[["node", "root_time_now", count_col]].dropna().copy()
    if sub.empty:
        return pd.DataFrame(columns=["node", "bin", "bin_start_ms", "bin_end_ms", "rate_pkts_per_s", "kind"])

    # enforce numeric types
    sub["root_time_now"] = pd.to_numeric(sub["root_time_now"], errors="coerce")
    sub[count_col] = pd.to_numeric(sub[count_col], errors="coerce")
    sub = sub.dropna()

    if sub.empty:
        return pd.DataFrame(columns=["node", "bin", "bin_start_ms", "bin_end_ms", "rate_pkts_per_s", "kind"])

    # diffs per node
    sub = sub.sort_values(["node", "root_time_now"])
    sub["delta"] = sub.groupby("node")[count_col].diff()
    # handle resets or negative noise
    sub["delta"] = sub["delta"].clip(lower=0)

    # define bin by the time of the "later" sample
    sub["bin"] = (sub["root_time_now"] // interval_ms).astype(int)

    # aggregate increments by (node, bin)
    agg = (
        sub.groupby(["node", "bin"], as_index=False)["delta"]
           .sum()
           .rename(columns={"delta": "sum_increments"})
    )

    # bin boundaries
    agg["bin_start_ms"] = agg["bin"] * interval_ms
    agg["bin_end_ms"]   = (agg["bin"] + 1) * interval_ms

    # rate in pkts/s
    bin_seconds = interval_ms / 1000.0
    agg["rate_pkts_per_s"] = agg["sum_increments"] / bin_seconds

    # add label for the counter type
    agg["kind"] = count_col

    # sort
    agg = agg.sort_values(["node", "bin"]).reset_index(drop=True)
    return agg[["node", "bin", "bin_start_ms", "bin_end_ms", "rate_pkts_per_s", "kind"]]

def throughput_compute_and_plot(
    df: pd.DataFrame, 
    csv_means_output: Path,
    dir_lines: Path,
    dir_boxes: Path
    )->None:
    # ---------- THROUGHPUT: rates per interval from raw counters ----------
    interval_ms = 1000  # adjust the window size (ms) here
    rate_cols = [c for c in ["server_sent", "server_received", "total_sent", "total_received"] if c in df.columns]

    thr_frames = []
    for col in rate_cols:
        thr_frames.append(_compute_throughput_per_interval(df, col, interval_ms=interval_ms))
    thr = pd.concat(thr_frames, ignore_index=True) if thr_frames else pd.DataFrame()

    if not thr.empty:
        # save CSV with rates
        thr_csv = csv_means_output.parent / f"cooja_throughput_{interval_ms}ms.csv"
        thr.to_csv(thr_csv, index=False)

        # map label 2,3,... to also order nodes in throughput plots
        node_order = sorted(df["node"].astype(str).unique())
        node_to_labelnum = {n: i + 2 for i, n in enumerate(node_order)}
        thr["label"] = thr["node"].astype(str).map(node_to_labelnum)

        # plot one line chart per 'kind' (counter)
        kinds = thr["kind"].unique()
        for kind in kinds:
            kdf = thr[thr["kind"] == kind].copy()
            if kdf.empty:
                continue

            plt.figure(figsize=(12, 6))
            for node in sorted(kdf["node"].astype(str).unique()):
                ndf = kdf[kdf["node"].astype(str) == node].copy()
                # X-axis in seconds (window start)
                x_s = ndf["bin_start_ms"] / 1000.0
                plt.plot(
                    x_s, 
                    ndf["rate_pkts_per_s"], 
                    marker="o",          # show points
                    markersize=3,        # marker size
                    label=f"{_last_hextet_decimal(node)}"
                    )

            plt.title(f"Throughput ({kind}) — window={interval_ms} ms")
            plt.xlabel("time (s) — window start")
            plt.ylabel("rate (pkts/s)")
            plt.legend(
                loc="center left",
                bbox_to_anchor=(1.02, 0.5),
                fontsize="small",
                frameon=False
            )
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()

            safe_kind = re.sub(r"[^A-Za-z0-9_\-]+", "_", kind).strip("_")
            out_path = dir_lines / f"throughput_{safe_kind}_{interval_ms}ms.png"
            plt.savefig(out_path, dpi=150)
            plt.close()
            
        # --------- Boxplots of throughput (pkts/s) per node -----------
        kinds = thr["kind"].unique()
        for kind in kinds:
            kdf = thr[thr["kind"] == kind].copy()
            kdf = kdf.dropna(subset=["rate_pkts_per_s"])
            if kdf.empty:
                continue

            safe_kind = re.sub(r"[^A-Za-z0-9_\-]+", "_", kind).strip("_")
            out_path = dir_boxes / f"throughput_{safe_kind}_{interval_ms}ms.png"

            if sns is not None:
                fig, ax = plt.subplots(figsize=(12, 6))
                sns.boxplot(
                    data=kdf,
                    x="label",                    # nodes as 2,3,4,...
                    y="rate_pkts_per_s",
                    ax=ax, showcaps=True, width=0.6
                )
                # no legend (no hue)
                if ax.get_legend():
                    ax.get_legend().remove()
                ax.set_title(f"Throughput ({kind}) — window={interval_ms} ms")
                ax.set_xlabel("Node (numeric label starting from 2)")
                ax.set_ylabel("rate (pkts/s)")
                ax.grid(True, linestyle="--", alpha=0.5)
                sns.despine(ax=ax)
                fig.tight_layout()
                fig.savefig(out_path, dpi=150)
                plt.close(fig)
            else:
                # Fallback without seaborn
                bdf = kdf[["label", "rate_pkts_per_s"]].dropna().copy()
                # categories ordered by label
                cats = sorted(bdf["label"].unique())
                data = [bdf.loc[bdf["label"] == c, "rate_pkts_per_s"].values for c in cats]

                fig, ax = plt.subplots(figsize=(12, 6))
                ax.boxplot(data, patch_artist=True, widths=0.6, showcaps=True)
                ax.set_xticks(range(1, len(cats) + 1))
                ax.set_xticklabels([str(c) for c in cats])
                ax.set_title(f"Throughput ({kind}) — window={interval_ms} ms (non-seaborn)")
                ax.set_xlabel("Node (numeric label starting from 2)")
                ax.set_ylabel("rate (pkts/s)")
                ax.grid(True, linestyle="--", alpha=0.5)
                fig.tight_layout()
                fig.savefig(out_path, dpi=150)
                plt.close(fig)
