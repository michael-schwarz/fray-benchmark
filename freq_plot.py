import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_interrupt_set(interrupt_points):
    """
    Convert one interruptPoints list into a hashable canonical representation.

    Sorting makes the representation order-independent, so the same set
    in different orders is counted together.
    """
    return tuple(sorted((item["klass"], item["line"]) for item in interrupt_points))


def pretty_label(interrupt_set):
    if not interrupt_set:
        return "{}"
    return "\n".join(f"{klass}:{line}" for klass, line in interrupt_set)


def count_sets(data):
    """
    Count frequency of each interruptPoints set using entry['count'].
    """
    counter = Counter()

    for entry in data:
        interrupt_set = normalize_interrupt_set(entry.get("interruptPoints", []))
        count = entry.get("count", 0)
        counter[interrupt_set] += count

    return counter


def plot_counts(labels, values1, values2, name1, name2, output, log_scale=False):
    x = np.arange(len(labels))
    width = 0.38

    fig_width = max(12, len(labels) * 1.2)
    plt.figure(figsize=(fig_width, 7))

    # Plot only nonzero bars for each file
    x1 = [x[i] - width / 2 for i, v in enumerate(values1) if v > 0]
    y1 = [v for v in values1 if v > 0]

    x2 = [x[i] + width / 2 for i, v in enumerate(values2) if v > 0]
    y2 = [v for v in values2 if v > 0]

    plt.bar(x1, y1, width, label=name1)
    plt.bar(x2, y2, width, label=name2)

    plt.xlabel("Interrupt point sets")
    plt.ylabel("Frequency" + (" (log scale)" if log_scale else ""))
    plt.title(
        "Frequency of interrupt point sets by file"
        + (" (log scale)" if log_scale else "")
    )

    if log_scale:
        plt.yscale("log")

    plt.xticks(x, labels, rotation=60, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()

    print(f"Saved plot to {output}")


def main(
    file1,
    file2,
    linear_output="interrupt_set_comparison.png",
    log_output="interrupt_set_comparison_log.png",
    top_n=None,
):
    data1 = load_json(file1)
    data2 = load_json(file2)

    counts1 = count_sets(data1)
    counts2 = count_sets(data2)

    all_sets = set(counts1) | set(counts2)
    if not all_sets:
        print("No interrupt point sets found.")
        return

    # Sort by combined frequency descending
    sorted_sets = sorted(
        all_sets,
        key=lambda s: counts1.get(s, 0) + counts2.get(s, 0),
        reverse=True,
    )

    if top_n is not None:
        sorted_sets = sorted_sets[:top_n]

    labels = [pretty_label(s) for s in sorted_sets]
    values1 = [counts1.get(s, 0) for s in sorted_sets]
    values2 = [counts2.get(s, 0) for s in sorted_sets]

    name1 = Path(file1).stem
    name2 = Path(file2).stem

    plot_counts(labels, values1, values2, name1, name2, linear_output, log_scale=False)
    plot_counts(labels, values1, values2, name1, name2, log_output, log_scale=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python plot_interrupt_sets.py file1.json file2.json "
            "[linear_output.png] [log_output.png] [top_n]"
        )
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    linear_output = sys.argv[3] if len(sys.argv) > 3 else "interrupt_set_comparison.png"
    log_output = (
        sys.argv[4] if len(sys.argv) > 4 else "interrupt_set_comparison_log.png"
    )
    top_n = int(sys.argv[5]) if len(sys.argv) > 5 else None

    main(file1, file2, linear_output, log_output, top_n)
