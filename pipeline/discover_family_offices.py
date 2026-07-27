"""
SEC EDGAR full-text discovery of candidate family offices.

Discovery is not proof: a filing mention does not confirm the entity is a
family office. Candidates must be verified from a separate source.
"""

import re
import time
import json
import requests

# SEC fair-access policy requires a descriptive User-Agent with contact info.
CONTACT_EMAIL = "your-email@example.com"
HEADERS = {
    "User-Agent": f"Atrium Research {CONTACT_EMAIL}",
    "Accept": "application/json",
}
BASE = "https://efts.sec.gov/LATEST/search-index"
CIK_RE = re.compile(r"\(CIK\s*(\d{10})\)")


def search(query, forms=None, size=50, frm=0):
    params = {"q": query, "size": size, "from": frm}
    if forms:
        params["forms"] = forms
    r = requests.get(BASE, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def parse_hits(data):
    rows = []
    for h in data.get("hits", {}).get("hits", []):
        src = h.get("_source", {})
        names = src.get("display_names") or []
        raw = names[0] if names else "(unknown)"
        cik_m = CIK_RE.search(raw)
        rows.append({
            "entity": CIK_RE.sub("", raw).strip(" ()"),
            "cik": cik_m.group(1) if cik_m else None,
            "form": src.get("root_form") or src.get("file_type"),
            "filed": src.get("file_date"),
            "accession": (h.get("_id") or "").split(":")[0],
        })
    return rows


def discover(queries, forms=None):
    seen = {}
    for q in queries:
        try:
            data = search(q, forms=forms, size=50)
        except Exception as e:
            print(f"  ! query {q!r} failed: {e}")
            continue
        total = data.get("hits", {}).get("total", {}).get("value")
        rows = parse_hits(data)
        for row in rows:
            row["discovered_via"] = q
            key = row["cik"] or row["entity"].lower()
            seen.setdefault(key, row)
        print(f"  {q!r}: {total} filings mention this; {len(rows)} on page 1")
        time.sleep(0.3)  # polite: well under SEC's 10 req/s guideline
    return list(seen.values())


if __name__ == "__main__":
    QUERIES = [
        '"single family office"',
        '"single-family office"',
        '"our family office"',
    ]
    print("Discovering candidate family offices from SEC filings...\n")
    candidates = discover(QUERIES)

    print(f"\nDISCOVERED {len(candidates)} unique candidates "
          f"(NOT yet verified as family offices):\n")
    for c in candidates[:30]:
        cik = c["cik"] or "----------"
        print(f"  {c['entity'][:46]:48s} CIK {cik}  {c['form'] or '?':8s} {c['filed'] or ''}")

    with open("candidates.json", "w") as f:
        json.dump(candidates, f, indent=2)
    print(f"\nSaved {len(candidates)} candidates to candidates.json")
