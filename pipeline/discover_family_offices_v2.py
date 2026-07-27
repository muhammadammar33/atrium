"""
Higher-precision SEC discovery scoped to forms a family office files itself.

v1 phrase search had ~1/75 precision (press mentions, subject/filer inversion).
v2 searches within 13F-HR, 40-APP, and Form D so the filer is the candidate.
Still discovery, not proof — verify each hit from a separate source.

EDGAR skews toward larger offices (13F needs >$100M); smaller SFOs are reached
via the IRS 990-PF trail instead.
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

# (query, forms, signal_label, priority) — higher priority = stronger signal
STRATEGIES = [
    ('"family office"', "13F-HR", "strong: 13F holdings filer (investment manager)", 3),
    ('"single family office"', "40-APP", "strong: exemptive application", 3),
    ('"family office"', "D", "weak: Form D private placement", 1),
]


def search(query, forms, size=100):
    params = {"q": query, "forms": forms, "size": size}
    r = requests.get(BASE, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def parse_hits(data):
    rows = []
    for h in data.get("hits", {}).get("hits", []):
        src = h.get("_source", {})
        names = src.get("display_names") or []
        raw = names[0] if names else "(unknown)"
        m = CIK_RE.search(raw)
        rows.append({
            "entity": CIK_RE.sub("", raw).strip(" ()"),
            "cik": m.group(1) if m else None,
            "form": src.get("root_form") or src.get("file_type"),
            "filed": src.get("file_date"),
            "accession": (h.get("_id") or "").split(":")[0],
        })
    return rows


def discover():
    seen = {}
    for query, forms, label, priority in STRATEGIES:
        try:
            data = search(query, forms)
        except Exception as e:
            print(f"  ! {forms} / {query!r} failed: {e}")
            continue
        total = data.get("hits", {}).get("total", {}).get("value")
        rows = parse_hits(data)
        print(f"  {forms:8s} + {query:24s}: {total} filings, {len(rows)} on page 1")
        for row in rows:
            row["discovered_via"] = f"{forms} | {query}"
            row["signal"] = label
            row["signal_priority"] = priority
            key = row["cik"] or row["entity"].lower()
            if key not in seen or priority > seen[key]["signal_priority"]:
                seen[key] = row
        time.sleep(0.3)
    return list(seen.values())


if __name__ == "__main__":
    print("Discovering family offices via forms they file themselves...\n")
    candidates = discover()
    candidates.sort(key=lambda x: -x["signal_priority"])

    print(f"\n{len(candidates)} unique candidates (verify each separately):\n")
    for c in candidates:
        cik = c["cik"] or "----------"
        strong = "***" if c["signal_priority"] >= 3 else "   "
        print(f" {strong} {c['entity'][:44]:46s} CIK {cik}  {c['form'] or '?':8s} {c['filed'] or ''}")

    with open("candidates_v2.json", "w") as f:
        json.dump(candidates, f, indent=2)
    print(f"\nSaved to candidates_v2.json. The *** rows are the high-signal ones "
          f"to verify first.")
