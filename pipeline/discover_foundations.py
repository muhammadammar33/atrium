"""
Second discovery trail via IRS 990-PF private foundations (ProPublica API).

A foundation is not a family office — it is a lead on a wealthy family that
may operate an SFO. Yields a multi-source dataset (EDGAR + IRS), ranked by
foundation assets.
"""

import time
import json
import requests

CONTACT_EMAIL = "your-email@example.com"
HEADERS = {"User-Agent": f"Atrium Research {CONTACT_EMAIL}"}
SEARCH = "https://projects.propublica.org/nonprofits/api/v2/search.json"
ORG = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

QUERIES = ['"family foundation"', '"family trust"']
MAX_DETAIL = 60  # cap per-org detail lookups


def search_orgs(query, max_pages=4):
    orgs = []
    for p in range(max_pages):
        try:
            r = requests.get(SEARCH, params={"q": query, "page": p},
                             headers=HEADERS, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  ! search page {p} for {query!r} failed: {e}")
            break
        orgs += data.get("organizations", [])
        if p + 1 >= data.get("num_pages", 1):
            break
        time.sleep(0.3)
    return orgs


def detail(ein):
    r = requests.get(ORG.format(ein=ein), headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def latest_assets_and_pf(det):
    """Return (assets, is_private_foundation) from an org detail response."""
    fils = det.get("filings_with_data") or []
    assets, is_pf = None, False
    for f in fils:
        # ProPublica formtype: 0=990, 1=990-EZ, 2=990-PF
        if f.get("formtype") == 2 or str(f.get("form_type", "")).endswith("PF"):
            is_pf = True
        for field in ("totassetsend", "totassetsendofyear", "totassets"):
            if assets is None and f.get(field):
                assets = f.get(field)
    return assets, is_pf


def discover():
    seen = {}
    for q in QUERIES:
        orgs = search_orgs(q)
        print(f"  {q!r}: {len(orgs)} organizations found")
        for o in orgs:
            ein = o.get("ein")
            if ein and ein not in seen:
                seen[ein] = {
                    "ein": ein,
                    "name": o.get("name"),
                    "city": o.get("city"),
                    "state": o.get("state"),
                    "discovered_via": f"ProPublica 990 search | {q}",
                }
    leads = list(seen.values())
    print(f"\n{len(leads)} unique candidate foundations. "
          f"Enriching the first {MAX_DETAIL} with size + 990-PF check...\n")

    enriched = []
    for lead in leads[:MAX_DETAIL]:
        try:
            assets, is_pf = latest_assets_and_pf(detail(lead["ein"]))
            lead["assets"] = assets
            lead["is_private_foundation"] = is_pf
        except Exception as e:
            lead["assets"], lead["is_private_foundation"] = None, None
        enriched.append(lead)
        time.sleep(0.25)

    pf = [x for x in enriched if x.get("is_private_foundation")]
    pf.sort(key=lambda x: (x["assets"] or 0), reverse=True)
    return pf, enriched


if __name__ == "__main__":
    print("Discovering wealthy-family leads via 990-PF foundations...\n")
    pf, allrows = discover()

    print(f"\n{len(pf)} confirmed private foundations, ranked by assets:\n")
    for x in pf[:30]:
        a = f"${(x['assets'] or 0)/1e6:,.0f}M" if x.get("assets") else "   ?   "
        print(f"  {a:>10s}  {(x['name'] or '')[:44]:46s} {x['city']}, {x['state']}")

    json.dump(allrows, open("foundation_leads.json", "w"), indent=2)
    print(f"\nSaved to foundation_leads.json. These are LEADS (wealthy families), "
          f"not confirmed family offices.")
