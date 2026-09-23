# jobwatch-scripts

Cheap replacements for expensive `browserUse` job scans.

**Tracks (additive):**
- People-managers in Warsaw (~10 mi) + Plymouth — ~$80–90k band heuristic (not hard-gated in code)
- Entry/mid **Computer Systems Analyst** titles in the same pockets (no $80k hard floor; prefer HS/no-bachelor walls when education is present)

Notify pockets: `warsaw`, `plymouth`, `warsaw_csa`, `plymouth_csa`. Exit `10` only when **all** of those are empty (scan) or have no **new** hits (diff).

- `scan.py` — multi-source HTTP scan + JobWatch filters
- `lib/` — Ultipro, Workday CXS, ADP, Phenom, TalentBrew, Hershey SF HTML, LinkedIn guest, filters
- `fetch_*.py` — one-off demos / snippets
- `SOURCES.md` — employer → scriptable endpoint map
- `out/` — JSON reports (gitignored)

```bash
python3 scan.py --json out/scan.json --all
# optional LinkedIn guest CSA sweep is on by default; omit with:
# python3 scan.py --source 1stsource,everwise,slate,lakecity,zimmer,hershey,ats,interra,purity --json out/scan.json
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

Exit `10` = no new manager **or** CSA pocket hits (stay quiet). Exit `0` = something new to ping.

CSA title match is tight (`Systems Analyst`, `Computer Systems Analyst`, `IT Systems Analyst`, `Jr/Junior Systems Analyst`, `IT Analyst`, `Business/Application Systems Analyst`). Help Desk / generic IT Support are excluded unless the title is clearly systems-analyst. Senior/Lead/Principal CSA titles in-pocket land in `other` (visible with `--all`), not the CSA notify buckets.
