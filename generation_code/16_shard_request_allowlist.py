#!/usr/bin/env python3
from pathlib import Path
import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("boundaries", nargs="+", type=int)
    args = parser.parse_args()
    values = [line.strip() for line in args.input_path.read_text().splitlines() if line.strip()]
    points = [0, *args.boundaries, len(values)]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index, (start, end) in enumerate(zip(points, points[1:]), start=1):
        if start >= end:
            continue
        (args.output_dir / f"shard_{index}_{start}_{end}.txt").write_text("\n".join(values[start:end]) + "\n")
    print(f"sharded {len(values)} request IDs at {points}")


if __name__ == "__main__":
    main()
