# JobWatch scriptable sources

HTTP/API first. Browser only when listed under **Needs browser**.
Probed 2026-09-06 (America/Indiana/Indianapolis).

## Working without browser

| Employer | Method | Endpoint / pattern | Filters | Script / module | Sample shape |
|---|---|---|---|---|---|
| **1st Source Bank** | Ultipro JSON POST | `https://recruiting.ultipro.com/STS1000SCO/JobBoard/bdcbc22d-c568-4b9f-bc84-421f9522fd47/JobBoardView/LoadSearchResults` (warm board GET first) | `opportunitySearch.QueryString`; `GetFilters` for physical locations | `lib/ultipro.py` → `fetch_1st_source` | `{"opportunities":[{"Id","Title","Locations","RequisitionNumber",...}],"totalCount":N}` |
| **Interra CU** | Ultipro JSON POST | `https://recruiting2.ultipro.com/INT1063INTCU/JobBoard/5786d0b7-c595-469a-b8c2-56d92566cc7b/JobBoardView/LoadSearchResults` | same Ultipro payload | `lib/ultipro.py` → `fetch_interra` | same |
| **Everwise CU** | Workday CXS POST | `https://ecu.wd12.myworkdayjobs.com/wday/cxs/ecu/Everwise_Careers/jobs` | `searchText`, `appliedFacets`, `limit`/`offset` | `lib/workday.py` | `{"total":N,"jobPostings":[{"title","externalPath","locationsText","postedOn",...}]}` |
| **Slate Auto** | Workday CXS POST | `https://recar.wd108.myworkdayjobs.com/wday/cxs/recar/SLATEcareers/jobs` | `searchText:"Warsaw"` works | `lib/workday.py` | same CXS |
| **Lake City Bank** | ADP GET JSON | `https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions?cid=4c0f5e63-d8a0-4686-b48c-977660d2dabc&ccId=9200753277202_3&lang=en_US&$top=50` | `$top`/`$skip`; cid/ccId from careers widget | `lib/adp.py` | `{"jobRequisitions":[{"requisitionTitle","postDate","itemID", locations...}]}` |
| **Zimmer Biomet** | Phenom POST | `https://careers.zimmerbiomet.com/widgets` body `ddoKey=refineSearch`, `selected_fields.state=["Indiana"]` | state/city/category facets | `lib/phenom.py` | `{"refineSearch":{"hits":N,"data":{"jobs":[{"title","city","state","jobId",...}]}}}` |
| **Hershey** | SF RMK HTML | `https://careers.thehersheycompany.com/search/?q=&locationsearch=Plymouth,%20IN` | `locationsearch`, `q`, `startrow` | `lib/hershey.py` | HTML `a.jobTitle-link` + `/job/...` paths (Plymouth FSQA Team Lead seen) |
| **ATS (Advanced Technology Services)** | TalentBrew AJAX | `https://jobs.advancedtech.com/en/search-jobs/results?...&Location=Indiana&RecordsPerPage=50` + `X-Requested-With: XMLHttpRequest` | Location / Keywords query params | `lib/talentbrew.py` | JSON `{results: "<html…h2>title</h2><span class=job-location>…"}` |
| **Purity Gas** | Static HTML | `https://www.puritygas.com/careers/` | none (page text) | `lib/html_careers.py` | may be empty if no Warsaw Branch Manager block currently posted |
| **LinkedIn (optional)** | Guest HTML | `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=manager&location=Warsaw,%20Indiana&start=0` | keywords/location/start | `fetch_linkedin_guest.py` | HTML job cards; fragile / ToS risk — prefer ATS |

### Ultipro request body

```json
{
  "opportunitySearch": {
    "Top": 50,
    "Skip": 0,
    "QueryString": "",
    "OrderBy": [{"Value": "postedDateDesc", "PropertyName": "PostedDate", "Ascending": false}],
    "Filters": []
  }
}
```

### Workday CXS body

```json
{"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
```

## Needs browser (or more RE)

| Employer | Why | Notes |
|---|---|---|
| **Walmart** | Next.js SPA; `/api/*` returns HTML shell; bot challenge on some hosts | Stocking Coach pattern — browserUse |
| **Pregis** | Dayforce at `https://jobs.dayforcehcm.com/pregis/CANDIDATEPORTAL`; discovered `POST /api/geo/pregis/jobposting/search` but **403** without their browser client | Browser fallback |
| **Wildman** | `secure*.entertimeonline.com` Career Search SPA; HTML shell only | Browser fallback |
| **Indeed** | RSS + search **403** | Do not scrape |
| Lake City **HTML** page alone | Widget is ADP JS — use `lib/adp.py` instead of page scrape | ADP path works |

## Run

```bash
cd /workspace/jobwatch-scripts
python3 scan.py --json out/scan.json
python3 scan.py --source lakecity,zimmer,hershey,ats --raw | head
python3 fetch_adp_lcb.py          # standalone demos also present
python3 fetch_hershey.py --location "Plymouth, IN"
```

Standalone demos (stdlib urllib): `fetch_*.py` + `common.py`. Canonical scan path is `scan.py` + `lib/`.
