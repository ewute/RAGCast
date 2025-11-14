"""Scrape lyrics for Epic: The Musical and save each song into its saga folder.

Creates one .txt file per song inside the saga directory (which you said you've
already created). The script will:
 - Parse https://www.allmusicals.com/e/epicthemusical.htm to map songs -> saga
 - Fetch each song page, extract the lyrics block, clean HTML, and write to
   <saga_folder>/<sanitized_title>.txt

Usage:
    python3 scrape_lyrics.py

Dependencies: requests, beautifulsoup4
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.allmusicals.com"
ALBUM_URL = "https://www.allmusicals.com/e/epicthemusical.htm"
SAGAS_DIR = Path(__file__).resolve().parent


def safe_filename(s: str) -> str:
    # Replace problematic characters and collapse whitespace
    s = s.strip()
    s = re.sub(r"[\\/:*?\"<>|]", "", s)
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ", "_")
    return s


def parse_album_list() -> List[Tuple[str, str, str]]:
    """Return list of tuples (saga, title, full_url) in order from album page."""
    resp = requests.get(ALBUM_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    list_section = soup.select_one("section.lyrics-list ol")
    if not list_section:
        raise RuntimeError("Could not find the lyrics list on album page")

    rows: List[Tuple[str, str, str]] = []
    current_saga = None
    for li in list_section.find_all("li", recursive=False):
        # act markers have class 'act' and contain a <strong><span>Saga Name</span></strong>
        if "act" in li.get("class", []):
            sp = li.find("span")
            if sp:
                current_saga = sp.get_text(strip=True)
            continue

        a = li.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href") or ""
        full = urljoin(BASE, href)
        rows.append((current_saga or "Unknown", title, full))

    return rows


def extract_lyrics_from_song_page(url: str) -> str:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    page_div = soup.find(id="page")
    if not page_div:
        # fallback: look for section.lyrics-content or div.lyrics-content-main-text
        page_div = soup.select_one("section.lyrics-content #page, .lyrics-content-main-text #page")
    if not page_div:
        # As last resort, pull whole body text
        page_div = soup.body
        if not page_div:
            raise RuntimeError(f"Could not find lyrics block in {url}")

    # Convert <br> to newlines and then extract text
    for br in page_div.find_all("br"):
        br.replace_with("\n")

    raw = page_div.get_text(separator="\n")

    # Remove trailing parts starting at common headings
    split_regex = re.compile(r"\n(?:Song Overview|Song Credits|Song Meaning|Song Meaning and Annotations|Song Overview and Annotations)", re.IGNORECASE)
    m = split_regex.search(raw)
    if m:
        raw = raw[: m.start()]

    # Also remove "Last Update" line if present
    raw = re.sub(r"Last Update:.*$", "", raw, flags=re.MULTILINE)

    # Collapse multiple blank lines to max two
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def main() -> int:
    print("Parsing album page for song -> saga mapping...")
    mapping = parse_album_list()
    print(f"Found {len(mapping)} songs. Starting to fetch lyrics...")

    for saga, title, url in mapping:
        saga_dir = SAGAS_DIR / saga
        if not saga_dir.exists():
            print(f"Saga folder not found for '{saga}', creating it: {saga_dir}")
            saga_dir.mkdir(parents=True, exist_ok=True)

        filename = safe_filename(title) + ".txt"
        out_path = saga_dir / filename
        if out_path.exists():
            print(f"Skipping existing: {out_path}")
            continue

        try:
            print(f"Fetching '{title}' -> {url}")
            lyrics = extract_lyrics_from_song_page(url)
        except Exception as exc:
            print(f"Failed to fetch '{title}': {exc}")
            continue

        if not lyrics:
            print(f"No lyrics found for '{title}' ({url})")
            continue

        out_path.write_text(lyrics, encoding="utf-8")
        print(f"Wrote {out_path} ({len(lyrics.splitlines())} lines)")

        # Be polite
        time.sleep(0.4)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
