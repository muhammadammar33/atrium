"""
Fetch raw material into a draft record for human classification.

Automates the boring work: SEC address/filings, website sentences that mention
family-office language, and foundation size/PDF links. Leaves fo_type,
proof_source, decision_makers, and confidence blank for judgment from evidence.
"""

import re
import json
import time
import requests
from pathlib import Path

# SEC fair-access policy requires a descriptive User-Agent with contact info.
CONTACT_EMAIL = "your-email@example.com"
HEADERS = {"User-Agent": f"Atrium Research {CONTACT_EMAIL}"}
SEC_SUB = "https://data.sec.gov/submissions/CIK{cik}.json"
PP_ORG = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

FO_KEYWORDS = ["single family office", "single-family office", "family office",
               "multi-family", "multi family", "no outside", "no institutional",
               "one family", "the family", "our clients", "families we serve"]


def fetch_website_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        return None, f"(fetch failed: {e})"
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", r.text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text), None


def evidence_sentences(text):
    """Surface short sentences that mention family-office keywords, for human review."""
    hits = []
    for s in re.split(r"(?<=[.!?])\s+", text or ""):
        low = s.lower()
        if 20 < len(s) < 280 and any(k in low for k in FO_KEYWORDS):
            hits.append(s.strip())
    # de-dup, cap
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out[:8]


def sec_enrich(cik):
    r = requests.get(SEC_SUB.format(cik=str(cik).zfill(10)), headers=HEADERS, timeout=30)
    r.raise_for_status()
    s = r.json()
    biz = (s.get("addresses") or {}).get("business") or {}
    recent = (s.get("filings") or {}).get("recent") or {}
    return {
        "official_name": s.get("name"),
        "city": biz.get("city"), "state": biz.get("stateOrCountry"),
        "former_names": [f.get("name") for f in (s.get("formerNames") or [])],
        "forms": sorted(set(recent.get("form") or []))[:8],
    }


def pp_enrich(ein):
    r = requests.get(PP_ORG.format(ein=ein), headers=HEADERS, timeout=30)
    r.raise_for_status()
    d = r.json()
    org = d.get("organization") or {}
    fils = d.get("filings_with_data") or []
    nodata = d.get("filings_without_data") or []
    assets = next((f.get("totassetsend") for f in fils if f.get("totassetsend")), None)
    pdf = next((f.get("pdf_url") for f in (fils + nodata) if f.get("pdf_url")), None)
    return {
        "foundation_name": org.get("name"),
        "city": org.get("city"), "state": org.get("state"),
        "assets": assets, "latest_990pf_pdf": pdf,
    }


def blank_cell():
    return {"value": None, "source": None, "confidence": None}


def enrich(lead):
    draft = {
        "entity": lead.get("name", ""),
        "fo_type": {"value": None, "source": None, "confidence": None,
                    "_TODO": "you decide single/multi from the evidence below"},
        "family": None,
        "location": blank_cell(),
        "founded": blank_cell(),
        "aum": {"value": None, "note": None, "source": None, "confidence": None},
        "thesis": blank_cell(),
        "headcount": blank_cell(),
        "decision_makers": [],
        "firm_contact": {"website": lead.get("website"), "email": None, "phone": None,
                         "address": None, "linkedin": None, "source": None, "confidence": None},
        "identifiers": {"cik": lead.get("cik"), "ein": lead.get("ein")},
        "discovered_via": lead.get("discovered_via"),
        "proof_source": None,
        "record_confidence": None,
        "_raw_evidence": {},
    }

    if lead.get("cik"):
        try:
            sec = sec_enrich(lead["cik"])
            draft["location"] = {"value": None, "city": sec["city"], "state": sec["state"],
                                 "source": "SEC EDGAR submissions", "confidence": "high"}
            draft["_raw_evidence"]["sec"] = sec
        except Exception as e:
            draft["_raw_evidence"]["sec"] = f"(failed: {e})"
        time.sleep(0.2)

    if lead.get("ein"):
        try:
            draft["_raw_evidence"]["propublica"] = pp_enrich(lead["ein"])
        except Exception as e:
            draft["_raw_evidence"]["propublica"] = f"(failed: {e})"
        time.sleep(0.2)

    if lead.get("website"):
        text, err = fetch_website_text(lead["website"])
        draft["_raw_evidence"]["website_evidence"] = err or evidence_sentences(text)
        time.sleep(0.2)

    return draft


if __name__ == "__main__":
    infile = Path("leads_to_enrich.json")
    if not infile.exists():
        raise SystemExit("Create leads_to_enrich.json first (run build_leads.py).")
    leads = json.load(open(infile))
    drafts = []
    for lead in leads:
        print(f"  enriching: {lead.get('name')}")
        drafts.append(enrich(lead))
    json.dump(drafts, open("draft_records.json", "w"), indent=2)
    print(f"\nWrote {len(drafts)} draft records to draft_records.json.")
    print("Open it, READ each _raw_evidence block, then fill in fo_type, proof_source, "
          "family, decision_makers, and confidence yourself. Delete the _ fields when done.")
