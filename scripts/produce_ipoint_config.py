#!/usr/bin/env python3
"""Produce a lincheck interrupt-point strategy config.

Runs each lincheck benchmark with the random scheduler and each interrupt-point
strategy, then writes [["clazz", "strategy"], ...] for the first strategy whose
observed distinct interrupt-point/interleaving count is in (50, 1000).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from fray_benchmark.commons import ASSETS_PATH, OUTPUT_PATH
from fray_benchmark.utils import load_test_cases


STRATEGIES = ("ipoints", "klass-only-nonempty", "first-line-round50")
MIN_INTERLEAVINGS = 50
MAX_INTERLEAVINGS = 1000
TIMEOUT_SECONDS = 10 * 60


def load_json(path: Path) -> Any | None:
    try:
        with path.open() as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}") from exc


def observed_interleaving_count(report_dir: Path) -> int | None:
    data = load_json(report_dir / "interleaving_sequences.json")
    if data is None:
        return None
    if not isinstance(data, list):
        raise RuntimeError(f"Expected a JSON list in {report_dir / 'interleaving_sequences.json'}")
    return len(data)


def strategy_run_name(base_name: str, strategy: str) -> str:
    return f"{base_name}/{strategy}"


def strategy_output_root(base_name: str, strategy: str) -> Path:
    return Path(OUTPUT_PATH) / strategy_run_name(base_name, strategy) / "lincheck" / "random"


def strategy_command(base_name: str, strategy: str, timeout: int, cpu: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "fray_benchmark",
        "run",
        "fray",
        "lincheck",
        "--name",
        strategy_run_name(base_name, strategy),
        "--scheduler",
        "random",
        "--iterations",
        "1",
        "--timeout",
        str(timeout),
        "--cpu",
        str(cpu),
        f"--extra-fray-arg=--interrupt-points-strategy={strategy}",
    ]


def run_strategy(strategy: str, args: argparse.Namespace) -> None:
    command = strategy_command(args.name, strategy, args.timeout, args.cpu)
    if args.force:
        strategy_root = strategy_output_root(args.name, strategy)
        if strategy_root.exists():
            shutil.rmtree(strategy_root)

    print(" ".join(command))
    if not args.dry_run:
        subprocess.run(command, check=True)


def collect_counts(base_name: str, strategy: str, classes: list[str]) -> dict[str, int | None]:
    iter_dir = strategy_output_root(base_name, strategy) / "iter-0"
    return {
        clazz: observed_interleaving_count(iter_dir / str(index) / "report")
        for index, clazz in enumerate(classes)
    }


def produce_config(args: argparse.Namespace) -> list[list[str]]:
    classes = load_test_cases(os.path.join(ASSETS_PATH, "lincheck.txt"))
    for strategy in STRATEGIES:
        run_strategy(strategy, args)
    if args.dry_run:
        return []

    by_strategy = {
        strategy: collect_counts(args.name, strategy, classes)
        for strategy in STRATEGIES
    }

    result: list[list[str]] = []
    for clazz in classes:
        counts: dict[str, int | None] = {}
        for strategy in STRATEGIES:
            count = by_strategy[strategy][clazz]
            counts[strategy] = count
            print(f"{clazz} {strategy}: {count if count is not None else 'missing'}")

        selected = None
        for strategy in STRATEGIES:
            count = counts[strategy]
            if count is not None and MIN_INTERLEAVINGS < count < MAX_INTERLEAVINGS:
                selected = strategy
                break
        if selected is None:
            raise RuntimeError(
                f"No strategy for {clazz} produced between "
                f"{MIN_INTERLEAVINGS + 1} and {MAX_INTERLEAVINGS - 1} observed interleavings"
            )
        result.append([clazz, selected])
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        default="ipoint-config",
        help="Base experiment name under the benchmark output directory.",
    )
    parser.add_argument(
        "--result",
        default="ipoint_config.json",
        help='Path for the output JSON file, formatted as [["clazz", "strategy"], ...].',
    )
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--cpu", type=int, default=1)
    parser.add_argument("--force", action="store_true", help="Delete and rerun existing reports.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    result = produce_config(args)
    if args.dry_run:
        return 0

    result_path = Path(args.result)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open("w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(f"Wrote {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
