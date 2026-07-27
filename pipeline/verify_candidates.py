"""
Entity confirmation and enrichment from EDGAR submissions (automatable half).

Confirms each candidate CIK is a real filer and attaches location / filing
history. Does not decide single- vs multi-family — that judgment uses a
second source (firm website / ADV); empty classification fields are staged
for that evidence trail.
"""

import json
import time
import requests

# SEC fair-access policy requires a descriptive User-Agent with contact info.
CONTACT_EMAIL = "your-email@example.com"
HEADERS = {"User-Agent": f"Atrium Research {CONTACT_EMAIL}",
           "Accept": "application/json"}
SUB_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def fetch_submission(cik):
    r = requests.get(SUB_URL.format(cik=cik), headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def summarize(sub):
    biz = (sub.get("addresses") or {}).get("business") or {}
    recent = (sub.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    former = [f.get("name") for f in (sub.get("formerNames") or [])]
    return {
        "official_name": sub.get("name"),
        "former_names": former,
        "city": biz.get("city"),
        "state": biz.get("stateOrCountry"),
        "sic": sub.get("sic"),
        "sic_desc": sub.get("sicDescription"),
        "n_13f": sum(1 for f in forms if f.startswith("13F")),
        "form_types": sorted(set(forms))[:8],
        "latest_filing": dates[0] if dates else None,
    }


def verify(infile="candidates_v2.json", outfile="verified_candidates.json"):
    candidates = json.load(open(infile))
    out = []
    for c in candidates:
        cik = c.get("cik")
        rec = {
            "entity": c.get("entity"),
            "cik": cik,
            "discovered_via": c.get("discovered_via"),
            "signal": c.get("signal"),
            "official_name": None, "former_names": [], "city": None,
            "state": None, "sic": None, "sic_desc": None, "n_13f": None,
            "form_types": [], "latest_filing": None,
            # Staged for human classification from a second independent source.
            "is_family_office": None,        # True / False
            "fo_type": None,                 # "single" / "multi" / "not_fo"
            "classification_source": None,   # URL of the proof
            "classification_evidence": None, # short quote/paraphrase
            "classification_confidence": None,  # "high"/"medium"/"low"
        }
        if cik:
            try:
                rec.update(summarize(fetch_submission(cik)))
            except Exception as e:
                rec["official_name"] = f"(fetch failed: {e})"
            time.sleep(0.2)  # polite: well under SEC's 10 req/s guideline
        out.append(rec)

    json.dump(out, open(outfile, "w"), indent=2)
    print(f"Enriched {len(out)} candidates -> {outfile}\n")
    print(f"{'ENTITY':40s} {'CITY, ST':22s} {'#13F':>5s}  SIC DESC")
    print("-" * 90)
    for r in out:
        loc = f"{r['city'] or '?'}, {r['state'] or '?'}"
        print(f"{(r['official_name'] or r['entity'])[:38]:40s} {loc[:22]:22s} "
              f"{str(r['n_13f']):>5s}  {r['sic_desc'] or ''}")


if __name__ == "__main__":
    verify()
