# jobwatch-scripts

Cheap replacements for expensive `browserUse` job scans (Warsaw + Plymouth IN, management ~$80–90k).

- `scan.py` — multi-source HTTP scan + JobWatch filters
- `lib/` — Ultipro, Workday CXS, ADP, Phenom, TalentBrew, Hershey SF HTML, filters
- `fetch_*.py` — one-off demos / snippets
- `SOURCES.md` — employer → scriptable endpoint map
- `out/` — JSON reports

```bash
python3 scan.py --json out/scan.json --all
```

## Week-over-week diff

```bash
# After scan.py writes out/scan.json:
python3 jobwatch-diff.py --current out/scan.json --previous out/scan-prev.json --json out/diff.json

# First ever baseline (quiet):
python3 jobwatch-diff.py --current out/scan.json --previous out/scan-prev.json --bootstrap

# After you've notified (or confirmed a quiet week), lock baseline:
python3 jobwatch-diff.py --current out/scan.json --previous out/scan-prev.json --promote
```

Exit `10` = no new Warsaw/Plymouth manager hits (stay quiet). Exit `0` = something new to ping.
