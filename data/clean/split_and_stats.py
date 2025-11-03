"""Compute simple summary statistics and split character_lines.csv into train/test.

Usage:
    python3 split_and_stats.py [--test-size 0.2] [--seed 42]

Outputs:
 - train.csv and test.csv written next to `character_lines.csv`
 - prints summary stats to stdout
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict

BASE = Path(__file__).parent
INPUT = BASE / "character_lines_clean.csv"
TRAIN_OUT = BASE / "train.csv"
TEST_OUT = BASE / "test.csv"


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return [r for r in reader]


def summarize(rows: List[Dict[str, str]]) -> Dict:
    total = len(rows)
    sagas = Counter()
    songs = Counter()
    chars = Counter()
    chars_len = []
    words_len = []

    for r in rows:
        sagas[r["saga"]] += 1
        songs[(r["saga"], r["song"])] += 1
        chars[r["character"]] += 1
        txt = r.get("lines", "")
        chars_len.append(len(txt))
        words_len.append(len(txt.split()))

    stats = {
        "total_rows": total,
        "unique_sagas": len(sagas),
        "unique_songs": len({k for k in songs}),
        "unique_characters": len(chars),
        "rows_per_saga_top10": sagas.most_common(10),
        "top_characters": chars.most_common(10),
        "avg_chars_per_segment": (sum(chars_len) / total) if total else 0,
        "avg_words_per_segment": (sum(words_len) / total) if total else 0,
    }
    return stats


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        # still write header if we can
        with path.open("w", encoding="utf-8", newline="") as fh:
            fh.write("")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-size", type=float, default=0.2, help="Proportion for test set (0-1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args(argv)

    if not INPUT.exists():
        print(f"Input CSV not found at {INPUT}")
        return 2

    rows = read_rows(INPUT)
    print(f"Read {len(rows)} rows from {INPUT}")

    stats = summarize(rows)
    print("Summary stats:")
    print(json.dumps(stats, indent=2))

    # Split
    random.seed(args.seed)
    indices = list(range(len(rows)))
    random.shuffle(indices)
    test_count = max(1, int(len(rows) * args.test_size))
    test_idx = set(indices[:test_count])

    train_rows = [rows[i] for i in range(len(rows)) if i not in test_idx]
    test_rows = [rows[i] for i in range(len(rows)) if i in test_idx]

    write_csv(TRAIN_OUT, train_rows)
    write_csv(TEST_OUT, test_rows)

    print(f"Wrote {len(train_rows)} rows to {TRAIN_OUT}")
    print(f"Wrote {len(test_rows)} rows to {TEST_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
