"""Normalize saved lyrics files and extract per-character lines.

This script does three things:
 1. Fixes spacing in the .txt lyrics files saved under each saga folder.
 2. Normalizes speaker bracket tokens, e.g.:
      [ODYSSEUS, spoken] -> [ODYSSEUS]
      [HERMES giggles]   -> [HERMES]
      [ODYSSEUS & CIRCE] -> [ODYSSEUS, CIRCE]
      [BOTH]             -> expanded to the explicit named characters in that song
 3. Produces `character_lines.csv` with columns: saga,song,character,lines

Usage:
    python3 normalize_and_extract.py

Backups: the script writes corrected files in-place, but saves a `.bak` of the
original if the file didn't already have one.

Dependencies: only Python stdlib.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parent
OUT_CSV = ROOT / "character_lines.csv"

SPEAKER_RE = re.compile(r"\[([^\]]+)\]")

# Tokens we treat as generic groups
GENERIC_GROUPS = {"SOLDIERS", "ENSEMBLE", "CHORUS", "COMPANY", "MEN", "WOMEN", "ALL", "BOTH"}


def clean_whitespace(text: str) -> str:
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing spaces on each line
    lines = [ln.rstrip() for ln in text.split("\n")]
    # Collapse multiple spaces to one inside lines
    lines = [re.sub(r"[ \t]{2,}", " ", ln) for ln in lines]
    text = "\n".join(lines)
    # Collapse 3+ blank lines into two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Trim start/end
    return text.strip() + "\n"


def extract_named_candidates(text: str) -> List[str]:
    """Scan speaker tokens and return ordered unique named candidates (uppercase entries).

    This does not perform final normalization; it heuristically extracts
    uppercase-name-like fragments from bracket tokens so we know how to expand BOTH/ALL.
    """
    names: List[str] = []
    for m in SPEAKER_RE.finditer(text):
        inner = m.group(1)
        parts = re.split(r"[,/\\&]|\band\b", inner, flags=re.IGNORECASE)
        for p in parts:
            p = re.sub(r"\(.*?\)", "", p).strip()
            if not p:
                continue
            # truncate at first lowercase word (e.g. 'HERMES giggles' -> 'HERMES')
            low = re.search(r"\b[a-z]{2,}\b", p)
            if low:
                p = p[: low.start()].strip()
            # capture sequences of uppercase words
            m2 = re.match(r"^([A-Z0-9'’\-]+(?:\s+[A-Z0-9'’\-]+)*)", p)
            if m2:
                cand = m2.group(1).strip()
                if cand and cand not in names:
                    names.append(cand)
            else:
                # if token itself is ALL/BOTH or similar, include uppercased
                up = p.strip().upper()
                if up in {"ALL", "BOTH"}:
                    if up not in names:
                        names.append(up)
    return names


def normalize_token(inner: str, named_list: List[str]) -> str:
    """Normalize the inside of a bracket token and expand BOTH/ALL based on named_list."""
    parts = re.split(r"[,/\\&]|\band\b", inner, flags=re.IGNORECASE)
    out_parts: List[str] = []
    for p in parts:
        p0 = re.sub(r"\(.*?\)", "", p).strip()
        if not p0:
            continue
        # if contains lowercase descriptor, truncate
        low = re.search(r"\b[a-z]{2,}\b", p0)
        if low:
            p0 = p0[: low.start()].strip()
        if not p0:
            continue
        up = p0.upper()
        if up in {"BOTH", "ALL"}:
            # expand
            for n in named_list:
                if n not in out_parts:
                    out_parts.append(n)
        else:
            # take uppercase name fragment at start
            m = re.match(r"^([A-Z0-9'’\-]+(?:\s+[A-Z0-9'’\-]+)*)", up)
            if m:
                name = m.group(1).strip()
                if name not in out_parts:
                    out_parts.append(name)
            else:
                # fallback: use the raw cleaned token
                cand = up.strip()
                if cand and cand not in out_parts:
                    out_parts.append(cand)

    if not out_parts:
        return inner.strip()
    return ", ".join(out_parts)


def normalize_file(path: Path) -> Tuple[Path, int]:
    """Normalize a single file in-place (with .bak) and return path and number of tokens fixed."""
    text = path.read_text(encoding="utf-8")
    orig = text
    text = clean_whitespace(text)

    named = extract_named_candidates(text)

    def repl(m: re.Match) -> str:
        inner = m.group(1)
        normalized = normalize_token(inner, named)
        return f"[{normalized}]"

    new_text = SPEAKER_RE.sub(repl, text)

    # Save backup if not present
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(orig, encoding="utf-8")

    path.write_text(new_text, encoding="utf-8")
    # estimate tokens changed by comparing occurrences
    changed = sum(1 for _ in SPEAKER_RE.finditer(orig)) - sum(1 for _ in SPEAKER_RE.finditer(new_text))
    return path, abs(changed)


def parse_segments(text: str) -> List[Tuple[List[str], str]]:
    """Return list of (speakers, content) segments based on normalized [TOKENS]."""
    matches = list(SPEAKER_RE.finditer(text))
    if not matches:
        content = text.strip()
        return [(["NARRATION"], content)] if content else []

    segments: List[Tuple[List[str], str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        inner = m.group(1)
        parts = [p.strip() for p in inner.split(",") if p.strip()]
        segments.append((parts, content))
    return segments


def extract_all() -> int:
    rows = []
    total_files = 0
    total_fixed = 0

    for saga_dir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        # skip scripts
        if saga_dir.name.lower().endswith(".py"):
            continue
        for txt in sorted(saga_dir.glob("*.txt")):
            total_files += 1
            path, changed = normalize_file(txt)
            total_fixed += changed
            text = path.read_text(encoding="utf-8")
            segments = parse_segments(text)
            song = txt.stem.replace("_", " ")
            # Aggregate per character
            by_char: Dict[str, List[str]] = defaultdict(list)
            for speakers, content in segments:
                if not content:
                    continue
                for s in speakers:
                    key = s.title()
                    by_char[key].append(content)

            for character, segs in by_char.items():
                joined = "\n\n".join(segs)
                rows.append((saga_dir.name, song, character, joined))

    # write CSV
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["saga", "song", "character", "lines"])
        for r in rows:
            writer.writerow(r)

    print(f"Processed {total_files} files, fixed approx {total_fixed} tokens, wrote {len(rows)} rows to {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(extract_all())
