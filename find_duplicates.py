#!/usr/bin/env python3
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def normalize_interrupt_point(point: dict) -> tuple:
    """
    Convert one interrupt point dict into a hashable canonical tuple.
    Missing keys are normalized to None.
    """
    return (
        point.get("klass"),
        point.get("line"),
        point.get("klassAfter"),
        point.get("lineAfter"),
    )


def normalize_interrupt_points(points: list[dict]) -> tuple:
    """
    Normalize a whole interruptPoints list while ignoring order.

    We preserve multiplicity using Counter, so if the same interrupt point
    appears twice in one list, that is distinct from appearing once.
    """
    counts = Counter(normalize_interrupt_point(p) for p in points)

    # Sort using a comparison-safe key, since tuples may contain None.
    return tuple(
        sorted(
            counts.items(),
            key=lambda item: (
                str(item[0][0]),  # klass
                -10**18 if item[0][1] is None else item[0][1],  # line
                str(item[0][2]),  # klassAfter
                -10**18 if item[0][3] is None else item[0][3],  # lineAfter
                item[1],  # multiplicity
            ),
        )
    )


def find_duplicate_interrupt_points(data: list[dict]) -> dict:
    """
    Group records by normalized interruptPoints signature.
    Returns only groups with more than one record.
    """
    groups = defaultdict(list)

    for idx, record in enumerate(data):
        signature = normalize_interrupt_points(record.get("interruptPoints", []))
        groups[signature].append(
            {
                "index": idx,
                "count": record.get("count"),
                "firstIteration": record.get("firstIteration"),
                "interruptPoints": record.get("interruptPoints", []),
            }
        )

    return {sig: items for sig, items in groups.items() if len(items) > 1}


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <file.json>", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])

    try:
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, list):
        print("Error: expected top-level JSON array", file=sys.stderr)
        return 1

    duplicates = find_duplicate_interrupt_points(data)

    if not duplicates:
        print("No duplicate interruptPoints groups found.")
        return 0

    print(f"Found {len(duplicates)} duplicate interruptPoints group(s):\n")

    for group_num, records in enumerate(duplicates.values(), start=1):
        print(f"Group {group_num}: {len(records)} records")
        print("Representative interruptPoints:")
        print(json.dumps(records[0]["interruptPoints"], indent=2))

        print("Matching records:")
        for r in records:
            print(
                f"  - index={r['index']}, "
                f"count={r['count']}, "
                f"firstIteration={r['firstIteration']}"
            )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
