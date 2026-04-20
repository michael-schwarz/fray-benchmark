import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


TOTAL_ITER_RE = re.compile(r"Total iter:\s*(\d+)")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def extract_total_iter(log_path):
    with open(log_path, "r") as f:
        for line in f:
            match = TOTAL_ITER_RE.search(line)
            if match:
                return int(match.group(1))
    raise ValueError(f"Could not find 'Total iter' in {log_path}")


def cumulative_dense(data):
    max_iter = max((row["firstIteration"] for row in data), default=0)
    hits = [0] * (max_iter + 1)

    for row in data:
        hits[row["firstIteration"]] += 1

    ys = []
    running = 0
    for h in hits:
        running += h
        ys.append(running)

    xs = np.arange(max_iter + 1, dtype=int)
    ys = np.array(ys, dtype=float)
    return xs, ys


def load_run_curve(json_path):
    data = load_json(json_path)
    return cumulative_dense(data)


def pad_curve(curve, target_len):
    """
    Extend a cumulative curve to target_len by repeating its last value.
    target_len is the final number of x positions, so x will be 0..target_len-1.
    """
    if len(curve) == target_len:
        return curve
    if len(curve) == 0:
        return np.zeros(target_len, dtype=float)

    padded = np.empty(target_len, dtype=float)
    padded[: len(curve)] = curve
    padded[len(curve) :] = curve[-1]
    return padded


def collect_subject_runs(technique_dir, subject_num):
    """
    Reads all iter-* runs for one technique and one subject.

    Returns a list of dicts:
      {
        "curve": np.ndarray,
        "total_iter": int,
      }
    """
    technique_dir = Path(technique_dir)
    iter_dirs = sorted(
        [p for p in technique_dir.iterdir() if p.is_dir() and p.name.startswith("iter-")]
    )

    runs = []

    for iter_dir in iter_dirs:
        subject_dir = iter_dir / str(subject_num)
        json_path = subject_dir / "report/interleaving_sequences.json"
        log_path = subject_dir / "report/fray.log"

        if not json_path.exists():
            print(f"Skipping missing file: {json_path}")
            continue

        if not log_path.exists():
            print(f"Skipping missing log: {log_path}")
            continue

        try:
            _, curve = load_run_curve(json_path)
            total_iter = extract_total_iter(log_path)
        except Exception as e:
            print(f"Skipping {iter_dir}: {e}")
            continue

        runs.append({
            "curve": curve,
            "total_iter": total_iter,
        })

    return runs


def summarize_runs(runs):
    """
    Pad each run to its own total_iter + 1, then pad all runs to the
    maximum total_iter + 1 among the runs for this technique.

    This ensures the plotted mean/min/max extends all the way to Total iter.
    """
    if not runs:
        return None, None, None, None, None

    padded_runs = []
    total_iters = []

    for run in runs:
        curve = run["curve"]
        total_iter = run["total_iter"]

        # x runs from 0..total_iter inclusive
        target_len = total_iter + 1
        padded_curve = pad_curve(curve, target_len)

        padded_runs.append(padded_curve)
        total_iters.append(total_iter)

    max_total_iter = max(total_iters)
    final_len = max_total_iter + 1

    padded_runs = np.array([pad_curve(curve, final_len) for curve in padded_runs])

    x = np.arange(final_len, dtype=int)
    mean_y = padded_runs.mean(axis=0)
    min_y = padded_runs.min(axis=0)
    max_y = padded_runs.max(axis=0)

    return x, mean_y, min_y, max_y, max_total_iter


def generate_backoff_lines(max_x, backoff):
    if backoff <= 0:
        return []

    positions = []
    pos = backoff
    step = backoff

    while pos <= max_x:
        positions.append(pos)
        step *= 2
        pos += step

    return positions


def plot_subject(techniques, subject, backoff, output):
    plt.figure(figsize=(10, 6))
    global_max_x = 0

    for label, technique_path in techniques.items():
        if not technique_path.exists():
            print(f"Skipping missing technique folder: {technique_path}")
            continue

        runs = collect_subject_runs(technique_path, subject)
        if not runs:
            print(f"No valid runs found for {label}, subject {subject}")
            continue

        x, mean_y, min_y, max_y, technique_max_x = summarize_runs(runs)
        global_max_x = max(global_max_x, technique_max_x)

        line, = plt.plot(x, mean_y, label=f"{label} ({len(runs)})")
        plt.fill_between(x, min_y, max_y, alpha=0.2, color=line.get_color())

    if global_max_x == 0:
        global_max_x = 1

    for xpos in generate_backoff_lines(global_max_x, backoff):
        plt.axvline(x=xpos, linewidth=2.0, linestyle="--", color="black")

    plt.xlim(0, global_max_x)
    plt.xlabel("numberOfIteration")
    plt.ylabel("number of interruptPoints sets with firstIteration <= x")
    plt.title(f"Cumulative number of interruptPoints sets by iteration (subject {subject})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()

    return global_max_x


def plot_subject_log(techniques, subject, backoff, output, global_max_x):
    plt.figure(figsize=(10, 6))

    for label, technique_path in techniques.items():
        if not technique_path.exists():
            continue

        runs = collect_subject_runs(technique_path, subject)
        if not runs:
            continue

        x, mean_y, min_y, max_y, _ = summarize_runs(runs)

        # Log scale cannot display x=0. Drop that point entirely.
        positive_mask = x > 0
        x_log = x[positive_mask]
        mean_y_log = mean_y[positive_mask]
        min_y_log = min_y[positive_mask]
        max_y_log = max_y[positive_mask]

        if len(x_log) == 0:
            continue

        line, = plt.plot(x_log, mean_y_log, label=f"{label} ({len(runs)})")
        plt.fill_between(x_log, min_y_log, max_y_log, alpha=0.2, color=line.get_color())

    for xpos in generate_backoff_lines(global_max_x, backoff):
        if xpos > 0:
            plt.axvline(x=xpos, linewidth=2.0, linestyle="--", color="black")

    plt.xscale("log")
    plt.xlim(1, global_max_x)
    plt.xlabel("numberOfIteration")
    plt.ylabel("number of interruptPoints sets with firstIteration <= x")
    plt.title(f"Cumulative number of interruptPoints sets by iteration (subject {subject}, log x-axis)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=int, required=True, help="Subject number, e.g. 0..3")
    parser.add_argument(
        "--base-dir",
        type=str,
        default="/home/michael/Documents/software/fray-benchmark/output/realworld-apr20/lincheck",
        help="Base directory containing technique folders",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output plot path",
    )
    parser.add_argument(
        "--backoff",
        type=int,
        default=200,
        help="Initial dashed-line position; subsequent gaps double each time",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    subject = args.subject
    backoff = args.backoff

    techniques = {
        "random": base_dir / "random",
        "pos": base_dir / "pos",
        "llm-4": base_dir / "llm-4",
        "llm-8": base_dir / "llm-8",
    }

    output = args.output or f"plot-subject-{subject}.png"
    global_max_x = plot_subject(techniques, subject, backoff, output)

    output_path = Path(output)
    log_output = output_path.with_name(f"{output_path.stem}-log{output_path.suffix}")
    plot_subject_log(techniques, subject, backoff, str(log_output), global_max_x)

    print(f"Saved plot to {output}")
    print(f"Saved log plot to {log_output}")


if __name__ == "__main__":
    main()
