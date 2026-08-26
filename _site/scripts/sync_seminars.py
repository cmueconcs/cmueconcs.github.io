#!/usr/bin/env python3
"""Fetch the Econ-CS seminar schedule from the published Google Sheet and
regenerate the per-semester _data/seminars-*.yml files (and csv_exports/*.csv
mirrors) from it.

Each semester lives on its own tab of the same spreadsheet, published
individually via a stable gid. Add new semesters to SEMESTERS below as new
tabs are created.
"""

import csv
import io
import sys
import urllib.request
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "_data"
CSV_DIR = REPO_ROOT / "csv_exports"

BASE_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQLYHIrOcJQsKpLMRo046lVoGXxvkw7SsL1qiQ_u987IVRJvtSz7lk2F2ftQMQpvdXvYcOlzIEiO8gJ"
    "/pub?output=csv"
)

# name -> gid, taken from the "Publish to web" links for each tab.
SEMESTERS = {
    "spring-2025": "227899753",
    "fall-2025": "148325887",
    "spring-2026": "1914349264",
    "fall-2026": "0",
}

EXPECTED_FIELDS = {"date", "time", "room", "link", "speaker", "affiliation", "title"}


def fetch_csv(gid: str) -> str:
    url = f"{BASE_URL}&gid={gid}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_rows(csv_text: str):
    reader = csv.DictReader(io.StringIO(csv_text))
    fieldnames = set(reader.fieldnames or [])
    if fieldnames != EXPECTED_FIELDS:
        return None  # tab isn't in the expected schema (e.g. empty template)

    rows = []
    for row in reader:
        date = (row.get("date") or "").strip()
        if not date:
            continue
        rows.append(
            {
                "date": date,
                "time": (row.get("time") or "").strip(),
                "location": {
                    "room": (row.get("room") or "").strip(),
                    "link": (row.get("link") or "").strip(),
                },
                "speaker": (row.get("speaker") or "").strip(),
                "affiliation": (row.get("affiliation") or "").strip(),
                "title": (row.get("title") or "").strip(),
            }
        )
    return rows


def write_yaml(name: str, rows: list) -> Path:
    path = DATA_DIR / f"seminars-{name}.yml"
    chunks = []
    for row in rows:
        chunks.append(
            yaml.dump(
                [row],
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=100000,
            )
        )
    path.write_text("\n".join(chunks))
    return path


def write_csv_mirror(name: str, csv_text: str) -> Path:
    path = CSV_DIR / f"{name}.csv"
    path.write_text(csv_text)
    return path


def main():
    changed = []
    for name, gid in SEMESTERS.items():
        print(f"Fetching {name} (gid={gid})...")
        try:
            csv_text = fetch_csv(gid)
        except Exception as e:
            print(f"  ERROR fetching {name}: {e}", file=sys.stderr)
            continue

        rows = parse_rows(csv_text)
        if rows is None:
            print(f"  Skipping {name}: sheet columns don't match expected schema "
                  f"(likely an empty/template tab).")
            continue
        if not rows:
            print(f"  Skipping {name}: no data rows.")
            continue

        write_csv_mirror(name, csv_text)
        yaml_path = write_yaml(name, rows)
        print(f"  Wrote {len(rows)} seminars to {yaml_path.relative_to(REPO_ROOT)}")
        changed.append(name)

    if not changed:
        print("No semesters updated.")
    else:
        print(f"Updated: {', '.join(changed)}")


if __name__ == "__main__":
    main()
