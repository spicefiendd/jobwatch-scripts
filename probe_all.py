#!/usr/bin/env python3
"""Probe employer career/ATS endpoints; write findings to /tmp/probe_results.json"""
import json, re, sys
from urllib.parse import urljoin, quote
try:
    import requests
except ImportError:
    print("need requests"); sys.exit(1)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Accept": "application/json, text/html, */*"}
results = {}

def note(key, **kw):
    results[key] = kw
    print(f"\n=== {key}: {kw.get('status')} ===")
    if kw.get("sample"):
        print(str(kw["sample"])[:600])

# 1) Ultipro already known working - skip heavy
note("1st_source_ultipro", status="OK_known",
     endpoint="POST https://recruiting.ultipro.com/STS1000SCO/JobBoard/bdcbc22d-c568-4b9f-bc84-421f9522fd47/JobBoardView/LoadSearchResults",
     payload={"opportunitySearch":{"Top":50,"Skip":0,"QueryString":"","OrderBy":[{"Value":"postedDateDesc","PropertyName":"PostedDate","Ascending":False}],"Filters":[]}})

# 2) Lake City Bank - ADP
s = requests.Session(); s.headers.update(UA)
r = s.get("https://www.lakecitybank.com/about-us/careers/job-openings/", timeout=45)
adp_bits = {
    "cid": re.findall(r'cid["\s:=]+["\']?([A-Za-z0-9\-]+)', r.text, re.I)[:5],
    "ccId": re.findall(r'ccId["\s:=]+["\']?([A-Za-z0-9\-]+)', r.text, re.I)[:5],
    "customToken": re.findall(r'customToken["\s:=]+["\']([^"\']+)', r.text, re.I)[:5],
    "adp_urls": re.findall(r'https?://[^"\']*adp\.com[^"\']*', r.text, re.I)[:15],
    "data_attrs": re.findall(r'data-[a-z-]+=\"[^\"]+\"', r.text, re.I)[:30],
}
# ADP mdf job search common pattern
adp_candidates = []
for cid in adp_bits["cid"] or ["$EMPTY"]:
    for path in [
        f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={cid}&ccId=19000101_000001&lang=en_US",
        f"https://workforcenow.adp.com/mascsr/default/careercenter/public/events?cid={cid}",
    ]:
        adp_candidates.append(path)
# Also scrape script tags mentioning mascsr
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.I|re.S)
adp_script_hits = []
for sc in scripts:
    if "adp" in sc.lower() or "mascsr" in sc.lower() or "cid" in sc.lower():
        adp_script_hits.append(sc[:800])
note("lake_city_bank", status="HTML_OK", page_len=len(r.text), adp_bits=adp_bits, script_hits=adp_script_hits[:5],
     feed_url="https://www.lakecitybank.com/about-us/careers/job-openings/feed/")
rf = s.get("https://www.lakecitybank.com/about-us/careers/job-openings/feed/", timeout=30)
note("lake_city_bank_feed", status=rf.status_code, ctype=rf.headers.get("content-type"), sample=rf.text[:1000])

# Try ADP jobMeta / jobs API with discovered cids
for cid in set(adp_bits["cid"] or []):
    for url in [
        f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={cid}&ccId=19000101_000001&lang=en_US&selectedMenuKey=CurrentOpenings",
        f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={cid}",
    ]:
        try:
            rr = s.get(url, timeout=30, allow_redirects=True)
            print(f"ADP page {cid[:12]}... {rr.status_code} {len(rr.text)} final={rr.url[:100]}")
        except Exception as e:
            print("ADP err", e)

# Search ADP API patterns commonly used
# POST https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions/query
# needs cid cookie/header

with open("/tmp/lcb_page.html","w") as f: f.write(r.text)

# 3 Everwise / 10 Slate already known
note("everwise_workday", status="OK_known",
     endpoint="POST https://ecu.wd12.myworkdayjobs.com/wday/cxs/ecu/Everwise_Careers/jobs",
     payload={"appliedFacets":{},"limit":20,"offset":0,"searchText":""})
note("slate_workday", status="OK_known",
     endpoint="POST https://recar.wd108.myworkdayjobs.com/wday/cxs/recar/SLATEcareers/jobs",
     payload={"appliedFacets":{},"limit":20,"offset":0,"searchText":""})

# 4 Hershey
for url in [
    "https://careers.thehersheycompany.com/",
    "https://www.thehersheycompany.com/en_us/home/careers.html",
    "https://careers.hersheys.com/",
]:
    try:
        rr = s.get(url, timeout=30, allow_redirects=True)
        print(f"Hershey {url} -> {rr.status_code} {rr.url[:120]} len={len(rr.text)}")
        if "workday" in rr.url.lower() or "myworkdayjobs" in rr.text.lower():
            wd = re.findall(r'https?://[^"\']*myworkdayjobs\.com[^"\']*', rr.text)
            print("  workday urls", wd[:5])
        if rr.status_code == 200 and len(rr.text) > 500:
            note("hershey_landing", status=200, final_url=rr.url, sample=rr.text[:400],
                 workday=re.findall(r'https?://[^"\'\s]*myworkdayjobs\.com[^"\'\s]*', rr.text)[:8],
                 api=re.findall(r'https?://[^"\'\s]*(?:api|jobs|search)[^"\'\s]*', rr.text, re.I)[:15])
            break
    except Exception as e:
        print("Hershey fail", url, e)

# 5 ATS Advanced Technology Services
rr = s.get("https://jobs.advancedtech.com/", timeout=45)
print("ATS", rr.status_code, len(rr.text), rr.url)
ats_links = re.findall(r'https?://[^"\'\s]+', rr.text)
ats_interesting = [u for u in ats_links if re.search(r'job|api|workday|greenhouse|lever|icims|taleo|smartrecruiters|ultipro|adp', u, re.I)]
note("ats_advancedtech", status=rr.status_code, final_url=rr.url, interesting=ats_interesting[:20], sample=rr.text[:500],
     titles_guess=re.findall(r'<h[123][^>]*>([^<]{5,120})</h[123]>', rr.text)[:20])

# 6 Pregis
rr = s.get("https://www.pregis.com/careers/", timeout=45)
print("Pregis", rr.status_code, len(rr.text), rr.url)
pregis_int = [u for u in re.findall(r'https?://[^"\'\s]+', rr.text) if re.search(r'job|career|workday|greenhouse|lever|icims|taleo|smartrecruiters|ultipro|adp|myworkday', u, re.I)]
note("pregis", status=rr.status_code, final_url=rr.url, interesting=pregis_int[:25], sample=rr.text[:400])

# 7 Walmart
for url in [
    "https://careers.walmart.com/",
    "https://careers.walmart.com/us/jobs",
    "https://careers.walmart.com/api/search?q=&location=Warsaw%2C%20IN&brand=walmart",
]:
    try:
        rr = s.get(url, timeout=45)
        print(f"Walmart {url[:60]} {rr.status_code} {len(rr.content)} ct={rr.headers.get('content-type','')[:40]}")
        if "json" in (rr.headers.get("content-type") or "") or rr.text.strip().startswith("{"):
            note("walmart_api", status=rr.status_code, url=url, sample=rr.text[:800])
        elif rr.status_code == 200:
            apis = re.findall(r'https?://[^"\']*api[^"\']*', rr.text)[:10]
            print("  apis", apis)
    except Exception as e:
        print("Walmart err", e)

# 8 Purity Gas
rr = s.get("https://www.puritygas.com/careers/", timeout=45)
print("Purity", rr.status_code, len(rr.text))
pur_int = [u for u in re.findall(r'https?://[^"\'\s]+', rr.text) if re.search(r'job|career|workday|greenhouse|lever|icims|apply|ultipro|adp|bamboohr|paylocity', u, re.I)]
note("purity_gas", status=rr.status_code, interesting=pur_int[:20], titles=re.findall(r'<h[123][^>]*>([^<]{3,100})</h[123]>', rr.text)[:15], sample=rr.text[:400])

# 9 Wildman
rr = s.get("https://wildmanbg.com/career-openings/", timeout=45)
print("Wildman", rr.status_code, len(rr.text))
w_int = [u for u in re.findall(r'https?://[^"\'\s]+', rr.text) if re.search(r'job|career|workday|greenhouse|lever|icims|apply|ultipro|adp|bamboohr', u, re.I)]
note("wildman", status=rr.status_code, interesting=w_int[:20], titles=re.findall(r'<h[123][^>]*>([^<]{3,120})</h[123]>', rr.text)[:20],
     job_links=re.findall(r'href=\"([^\"]+)\"[^>]*>([^<]{5,100})', rr.text)[:30], sample=rr.text[:500])

# 11 Zimmer Biomet
for url in [
    "https://www.zimmerbiomet.com/en/careers.html",
    "https://careers.zimmerbiomet.com/",
    "https://www.zimmerbiomet.com/en/about-us/careers.html",
]:
    try:
        rr = s.get(url, timeout=45, allow_redirects=True)
        print(f"ZB {url} -> {rr.status_code} {rr.url[:100]} len={len(rr.text)}")
        wd = re.findall(r'https?://[^"\'\s]*myworkdayjobs\.com[^"\'\s]*', rr.text)
        if wd or "workday" in rr.url.lower():
            note("zimmer_biomet", status=rr.status_code, final_url=rr.url, workday=wd[:8], sample=rr.text[:300])
            break
        if rr.status_code == 200:
            ints = [u for u in re.findall(r'https?://[^"\'\s]+', rr.text) if re.search(r'job|career|workday|icims|taleo', u, re.I)]
            note("zimmer_biomet", status=rr.status_code, final_url=rr.url, interesting=ints[:15], sample=rr.text[:300])
            break
    except Exception as e:
        print("ZB fail", e)

# 12 Interra CU
for url in [
    "https://www.interracu.com/about/careers",
    "https://www.interracu.com/careers",
    "https://interracu.com/about-us/careers/",
]:
    try:
        rr = s.get(url, timeout=45, allow_redirects=True)
        print(f"Interra {url} -> {rr.status_code} {rr.url[:100]} len={len(rr.text)}")
        if rr.status_code == 200 and len(rr.text) > 1000:
            ints = [u for u in re.findall(r'https?://[^"\'\s]+', rr.text) if re.search(r'job|career|workday|ultipro|adp|icims|apply|paylocity|bamboohr', u, re.I)]
            note("interra", status=rr.status_code, final_url=rr.url, interesting=ints[:20], sample=rr.text[:400])
            with open("/tmp/interra.html","w") as f: f.write(rr.text)
            break
    except Exception as e:
        print("Interra fail", e)

# 13 Indeed / LinkedIn RSS
for label, url in [
    ("indeed_rss", "https://www.indeed.com/rss?q=manager&l=Warsaw%2C+IN&radius=25"),
    ("indeed_rss2", "https://rss.indeed.com/rss?q=manager&l=Warsaw%2C+IN"),
    ("linkedin_public", "https://www.linkedin.com/jobs/search/?keywords=manager&location=Warsaw%2C%20Indiana"),
]:
    try:
        rr = s.get(url, timeout=30, allow_redirects=True)
        print(f"{label} {rr.status_code} ct={rr.headers.get('content-type')} len={len(rr.content)} url={rr.url[:80]}")
        note(label, status=rr.status_code, final_url=rr.url, ctype=rr.headers.get("content-type"), sample=rr.text[:500])
    except Exception as e:
        note(label, status="ERR", error=str(e))

with open("/tmp/probe_results.json","w") as f:
    json.dump(results, f, indent=2, default=str)
print("\nWrote /tmp/probe_results.json keys:", list(results))
