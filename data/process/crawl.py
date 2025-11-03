"""Simple crawler to fetch specific link titles from
https://www.allmusicals.com/e/epicthemusical.htm

Outputs the matching link text and absolute URL for each title in the
hard-coded target list.

Dependencies: requests, beautifulsoup4

Usage:
	python3 crawl.py

"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


TARGET_TITLES: List[str] = [
	"The Troy Saga",
	"The Horse and the Infant",
	"Just A Man",
	"Full Speed Ahead",
	"Open Arms",
	"Warrior of the Mind",
	"The Cyclops Saga",
	"Polyphemus",
	"Survive",
	"Remember Them",
	"My Goodbye",
	"The Ocean Saga",
	"Storm",
	"Luck Runs Out",
	"Keep Your Friends Close",
	"Ruthlessness",
	"The Circe Saga",
	"Puppeteer",
	"Wouldn't You Like",
	"Done For",
	"There Are Other Ways",
	"The Underworld Saga",
	"The Underworld",
	"No Longer You",
	"Monster",
	"The Thunder Saga",
	"Suffering",
	"Different Beast",
	"Scylla",
	"Mutiny",
	"Thunder Bringer",
	"The Wisdom Saga",
	"Legendary",
	"Little Wolf",
	"We'd Be Fine",
	"Love in Paradise",
	"God Games",
	"The Vengeance Saga",
	"Not Sorry For Loving You",
	"Dangerous",
	"Charybdis",
	"Get in the Water",
	"600 Strike",
	"The Ithaca Saga",
	"The Challenge",
	"Hold Them Down",
	"Odysseus",
	"I Can't Help But Wonder",
	"Would You Fall In Love With Me Again",
]


def normalize_text(s: str) -> str:
	"""Normalize text for matching: straighten quotes, collapse whitespace, lower-case."""
	if s is None:
		return ""
	out = s
	# Straighten commonly used typographic quotes/apostrophes
	out = out.replace('’', "'")
	out = out.replace('‘', "'")
	out = out.replace('“', '"')
	out = out.replace('”', '"')

	# Collapse whitespace and lower
	out = " ".join(out.split())
	return out.strip().lower()


def fetch_and_extract(url: str, targets: List[str]) -> List[Dict[str, str]]:
	"""Fetch the given page and return list of matched {title, url} dicts.

	Matching is done by exact equality after normalization.
	"""
	try:
		resp = requests.get(url, timeout=15)
	except Exception as exc:  # pragma: no cover - runtime
		raise SystemExit(f"Failed to fetch {url}: {exc}")

	if resp.status_code != 200:
		raise SystemExit(f"Unexpected status code {resp.status_code} for {url}")

	soup = BeautifulSoup(resp.text, "html.parser")

	norm_targets = {normalize_text(t): t for t in targets}

	found = []
	seen = set()

	for a in soup.find_all("a"):
		text = a.get_text(strip=True)
		if not text:
			continue
		n = normalize_text(text)
		if n in norm_targets and n not in seen:
			href = a.get("href") or ""
			full = urljoin(url, href)
			found.append({"title": norm_targets[n], "url": full})
			seen.add(n)

	return found


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8", newline="") as fh:
		writer = csv.writer(fh)
		writer.writerow(["title", "url"])
		for r in rows:
			writer.writerow([r["title"], r["url"]])


def main(argv=None):
	argv = argv or sys.argv[1:]
	p = argparse.ArgumentParser(description="Crawl epicthemusical and extract specific links")
	p.add_argument("--out", "-o", help="Output CSV path", default=None)
	p.add_argument("--no-print", action="store_true", help="Don't print results to stdout")
	args = p.parse_args(argv)

	base = "https://www.allmusicals.com/e/epicthemusical.htm"
	results = fetch_and_extract(base, TARGET_TITLES)

	if not results:
		print("No matching titles found.")
		return 2

	out_path = Path(args.out) if args.out else Path(__file__).resolve().parent / "epicthemusical_links.csv"

	write_csv(out_path, results)

	if not args.no_print:
		for r in results:
			print(f"{r['title']} -> {r['url']}")

	print(f"Wrote {len(results)} rows to {out_path}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
