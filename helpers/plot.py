import csv
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from test.paths import RESULT_DIR

def load_results(csv_path: str):
    """
    Load the CSV results and return a DataFrame containing ONLY trial rows
    (i.e., skipping [Skip] and AVERAGE lines).
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    rows = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if not row:
                continue
            # skip lines like "[Skip] No feasible baseline CE ..."
            if row[0].startswith("[Skip]"):
                continue
            rows.append(row)

    df_all = pd.DataFrame(rows, columns=header)

    # keep only real trials (drop the AVERAGE rows)
    df = df_all[df_all["trial"] != "AVERAGE"].copy()

    # convert numeric columns
    num_cols = [
        "arg_count",
        "C_cap_size",
        "C_p_size",
        "C_q_size",
        "C_delta_size",
        "time_sec",
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # drop any rows without arg_count or metric value
    df = df.dropna(subset=["arg_count"])

    return df


def plot_metric(df: pd.DataFrame,
                metric: str,
                ylabel: str,
                log_y: bool = False,
                output: str = "plot.png"):
    """
    Scatter plot of trials + blue dashed mean line.
    Only mean is shown in legend.
    time_sec uses explicit ticks (0.01,0.1,1,10,100,1000).
    """

    fig, ax = plt.subplots(figsize=(7, 4))

    # 1) Scatter of trials (gray), no legend
    ax.scatter(
        df["arg_count"],
        df[metric],
        s=15,
        alpha=0.6,
        color="0.5"
    )

    # 2) Mean line (blue dashed)
    mean_by_args = (
        df.groupby("arg_count")[metric]
        .mean()
        .reset_index()
        .sort_values("arg_count")
    )

    ax.plot(
        mean_by_args["arg_count"],
        mean_by_args[metric],
        linestyle="--",   # <- dashed line as requested
        color="blue",
        linewidth=2.2,
        marker="o",
        markersize=6,
        label="mean"
    )

    ax.set_xlabel("number of arguments")
    ax.set_ylabel(ylabel)

    # Custom log y-axis for time
    if log_y:
        ax.set_yscale("log")
        ax.set_yticks([0.01, 0.1, 1, 10, 100, 1000])
        ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())

    # Grid + legend
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.7)
    ax.legend(loc="best")

    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)

def main(csv_path: str):
    df = load_results(csv_path)

    plot_dir = RESULT_DIR / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    plot_metric(
        df,
        metric="C_cap_size",
        ylabel="size of C_cap",
        log_y=False,
        output=str(plot_dir / "C_cap_size_vs_args.png"),
    )

    plot_metric(
        df,
        metric="C_p_size",
        ylabel="size of C_p",
        log_y=False,
        output=str(plot_dir / "C_p_size_vs_args.png"),
    )

    plot_metric(
        df,
        metric="C_q_size",
        ylabel="size of C_q",
        log_y=False,
        output=str(plot_dir / "C_q_size_vs_args.png"),
    )

    plot_metric(
        df,
        metric="C_delta_size",
        ylabel="size of C_delta",
        log_y=False,
        output=str(plot_dir / "C_delta_size_vs_args.png"),
    )

    plot_metric(
        df,
        metric="time_sec",
        ylabel="CPU time (seconds)",
        log_y=True,
        output=str(plot_dir / "time_sec_vs_args.png"),
    )


if __name__ == "__main__":
    csv_path = RESULT_DIR / "baseline_ce_results.csv"
    main(csv_path)
