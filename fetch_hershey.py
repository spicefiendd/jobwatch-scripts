#!/usr/bin/env python3
"""Hershey careers — SuccessFactors RMK HTML search (no browser)."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.hershey import fetch_hershey
from common import print_jobs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", default="Plymouth, IN")
    ap.add_argument("--q", default="")
    args = ap.parse_args()
    jobs = fetch_hershey(location=args.location, keywords=args.q)
    rows = [{"title": j.title, "location": j.location, "url": j.url} for j in jobs]
    print(f"# Hershey SF search location={args.location!r} n={len(rows)}\n")
    print_jobs(rows)

if __name__ == "__main__":
    main()
