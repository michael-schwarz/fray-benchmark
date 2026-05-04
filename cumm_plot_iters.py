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
    last_match = None

    with open(log_path, "r") as f:
        for line in f:
            match = TOTAL_ITER_RE.search(line)
            if match:
                if last_match is not None:
                    print(f"Warning: multiple 'Total iter' matches in {log_path}, using last one")
                last_match = int(match.group(1))

    if last_match is not None:
        return last_match

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
    if len(curve) == target_len:
        return curve
    if len(curve) == 0:
        return np.zeros(target_len, dtype=float)

    padded = np.empty(target_len, dtype=float)
    padded[: len(curve)] = curve
    padded[len(curve) :] = curve[-1]
    return padded


def collect_subject_runs(technique_dir, subject_num):
    technique_dir = Path(technique_dir)
    iter_dirs = sorted(
        [p for p in technique_dir.iterdir() if p.is_dir() and p.name.startswith("iter-")]
    )

    runs = []

    for iter_dir in iter_dirs:
        subject_dir = iter_dir / str(subject_num)
        json_path = subject_dir / "report/interleaving_sequences.json"
        log_path = subject_dir / "report/fray.log"

        if not json_path.exists() or not log_path.exists():
            continue

        try:
            _, curve = load_run_curve(json_path)
            total_iter = extract_total_iter(log_path)
        except Exception:
            continue

        runs.append({
            "curve": curve,
            "total_iter": total_iter
        })

    return runs


def summarize_runs(runs):
    if not runs:
        return None, None, None, None, None

    padded_runs = []
    total_iters = []

    for run in runs:
        curve = run["curve"]
        total_iter = run["total_iter"]

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

    count = 0

    positions = []
    pos = backoff
    step = backoff

    while pos <= max_x and count < 8:
        positions.append(pos)
        step *= 2
        pos += step
        count += 1

    return positions


def parse_subjects(arg):
    if ".." in arg:
        start, end = arg.split("..")
        return list(range(int(start), int(end) + 1))
    return [int(arg)]


def plot_standard(x, mean_y, min_y, max_y, label, runs):
    line, = plt.plot(x, mean_y, linewidth=2, label=f"{label} ({len(runs)})")

    for run in runs:
        run_x = np.arange(run["total_iter"] + 1, dtype=int)
        run_y = pad_curve(run["curve"], len(run_x))
        plt.plot(run_x, run_y, color=line.get_color(), alpha=0.7, linewidth=1)

    plt.fill_between(x, min_y, max_y, alpha=0.2, color=line.get_color())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=str, required=True)
    parser.add_argument(
        "--base-dir",
        type=str,
        default="/home/michael/Documents/software/fray-benchmark/output/realworld-apr30/lincheck",
        help="Base directory containing technique folders",
    )
    parser.add_argument("--output", type=str, default="plots/iset.png")
    parser.add_argument("--backoff", type=int, default=200)
    args = parser.parse_args()

    subjects = parse_subjects(args.subject)

    techniques = {
        "random": Path(args.base_dir) / "random",
        "pos": Path(args.base_dir) / "pos",
        "llm-4": Path(args.base_dir) / "llm-4",
        # "llm-4-tune": Path(args.base_dir) / "llm-4-tune",
        "llm-8": Path(args.base_dir) / "llm-8",
        # "llm-2": Path(args.base_dir) / "llm-2",
        # "llm-1": Path(args.base_dir) / "llm-1",
        # "pct3": Path(args.base_dir) / "pct3",
        # "surw": Path(args.base_dir) / "surw"
    }

    for subject in subjects:
        base_output = Path(args.output)
        stem = base_output.stem
        suffix = base_output.suffix or ".png"

        output = f"{stem}-subject-{subject}{suffix}"
        log_output = f"{stem}-subject-{subject}-log{suffix}"
        clip_output = f"{stem}-subject-{subject}-10k{suffix}"

        # ---------- standard plot ----------
        plt.figure(figsize=(10, 6))
        global_max_x = 0

        curves = {}

        for label, path in techniques.items():
            runs = collect_subject_runs(path, subject)
            if not runs:
                continue

            x, mean_y, min_y, max_y, max_x = summarize_runs(runs)
            global_max_x = max(global_max_x, max_x)

            curves[label] = (x, mean_y, min_y, max_y, runs)

            plot_standard(x, mean_y, min_y, max_y, label, runs)

        for xpos in generate_backoff_lines(global_max_x, args.backoff):
            plt.axvline(x=xpos, linestyle="--", color="black")

        plt.xlim(0, global_max_x)
        plt.xlabel("number of iterations")
        plt.ylabel("interruptPointSets with firstIteration <= x")
        plt.legend()
        plt.title(f"Subject {subject}")
        plt.grid(True)
        plt.savefig(output, dpi=200)
        plt.close()

        # ---------- log plot ----------
        plt.figure(figsize=(10, 6))

        for label, (x, mean_y, min_y, max_y, runs) in curves.items():
            x_log = x.copy()
            x_log[0] = 1
            plot_standard(x_log, mean_y, min_y, max_y, label, runs)

        for xpos in generate_backoff_lines(global_max_x, args.backoff):
            if xpos >= 1:
                plt.axvline(x=xpos, linestyle="--", color="black")

        plt.xscale("log")
        plt.xlim(1, global_max_x)
        plt.xlabel("number of iterations")
        plt.ylabel("interruptPointSets with firstIteration <= x")
        plt.legend()
        plt.title(f"Subject {subject} (log)")
        plt.grid(True)
        plt.savefig(log_output, dpi=200)
        plt.close()

        # ---------- 10k plot ----------
        plt.figure(figsize=(10, 6))

        visible_y_max = 0

        for label, (x, mean_y, min_y, max_y, runs) in curves.items():
            mask = x <= 10000
            if not np.any(mask):
                continue

            plot_standard(x[mask], mean_y[mask], min_y[mask], max_y[mask], label, runs)
            visible_y_max = max(visible_y_max, np.max(max_y[mask]))

        for xpos in generate_backoff_lines(10000, args.backoff):
            plt.axvline(x=xpos, linestyle="--", color="black")

        plt.xlim(0, 10000)
        plt.ylim(0, visible_y_max if visible_y_max > 0 else 1)
        plt.xlabel("number of iterations")
        plt.ylabel("interruptPointSets with firstIteration <= x")
        plt.legend()
        plt.title(f"Subject {subject} (0–10k)")
        plt.grid(True)
        plt.savefig(clip_output, dpi=200)
        plt.close()

        print(f"Saved plots for subject {subject}")


if __name__ == "__main__":
    main()
