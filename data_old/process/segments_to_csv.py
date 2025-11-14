"""Create a CSV with one row per speaker segment.

Output columns: saga, song, character, lyrics

Behavior:
 - Finds bracketed speaker tokens like [ODYSSEUS], [ENSEMBLE], [ODYSSEUS & POSEIDON]
 - For each token it captures the text until the next token (or EOF) as that segment's lyrics
 - Writes a row per segment; character field preserves the normalized token (commas used between names)

Usage:
    python3 segments_to_csv.py
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "segments.csv"

SPEAKER_RE = re.compile(r"\[([^\]]+)\]")


def normalize_token(inner: str) -> str:
    # Replace ampersand and slashes with commas, and collapse whitespace
    s = re.sub(r"[&/|]", ",", inner)
    s = re.sub(r"\band\b", ",", s, flags=re.IGNORECASE)
    parts = [p.strip() for p in s.split(",") if p.strip()]
    # Join with comma + space
    return ", ".join(parts)


def segments_from_text(text: str) -> List[tuple]:
    matches = list(SPEAKER_RE.finditer(text))
    if not matches:
        content = text.strip()
        return [("NARRATION", content)] if content else []

    segs = []
    for i, m in enumerate(matches):
        inner = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        token = normalize_token(inner)
        segs.append((token, content))
    return segs


def main() -> int:
    rows = []
    total = 0
    for saga_dir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        # skip python files directory
        if saga_dir.name.lower().endswith('.py'):
            continue
        for txt in sorted(saga_dir.glob('*.txt')):
            song = txt.stem.replace('_', ' ')
            text = txt.read_text(encoding='utf-8')
            segs = segments_from_text(text)
            for char, lyrics in segs:
                rows.append((saga_dir.name, song, char, lyrics))
                total += 1

    with OUT.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(['saga', 'song', 'character', 'lyrics'])
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {total} segment rows to {OUT}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
