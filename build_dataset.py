import json
import time
import requests
from pathlib import Path

CONTACT_EMAIL = "muhammadammar7747@gmail.com"
HEADERS = {"User-Agent": f"Atrium Research {CONTACT_EMAIL}", "Accept": "application/json"}
SEC_SUB = "https://data.sec.gov/submissions/CIK{cik}.json"
PP_ORG = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

DECISIONS = Path(__file__).parent / "decisions.json"
OUT = Path(__file__).parent / "family_offices.json"


def sec_enrich(cik):
    r = requests.get(SEC_SUB.format(cik=str(cik).zfill(10)), headers=HEADERS, timeout=30)
    r.raise_for_status()
    s = r.json()
    biz = (s.get("addresses") or {}).get("business") or {}
    return {"official_name": s.get("name"), "city": biz.get("city"),
            "state": biz.get("stateOrCountry"), "assets": None}


def pp_enrich(ein):
    r = requests.get(PP_ORG.format(ein=str(ein).replace("-", "")), headers=HEADERS, timeout=30)
    r.raise_for_status()
    d = r.json()
    org = d.get("organization") or {}
    fils = d.get("filings_with_data") or []
    assets = next((f.get("totassetsend") for f in fils if f.get("totassetsend")), None)
    return {"official_name": org.get("name"), "city": org.get("city"),
            "state": org.get("state"), "assets": assets}


def fmt_aum(assets):
    if not assets:
        return None
    if assets >= 1e9:
        return f"~${assets/1e9:.1f}B"
    return f"~${assets/1e6:,.0f}M"


def build_record(d):
    ident = d.get("identifiers") or {}
    ein, cik = ident.get("ein"), ident.get("cik")
    fb = d.get("manual_fallback") or {}
    prov = {}

    enriched, source_label = {}, None
    try:
        if ein:
            enriched, source_label = pp_enrich(ein), "IRS 990-PF via ProPublica (API)"
        elif cik:
            enriched, source_label = sec_enrich(cik), "SEC EDGAR submissions (API)"
    except Exception as e:
        prov["enrichment_error"] = str(e)

    # location: API-derived if available, else human fallback
    if enriched.get("city"):
        city, state = enriched["city"], enriched["state"]
        loc_source, prov["location"] = source_label, "api"
    else:
        city, state = fb.get("city"), fb.get("state")
        loc_source, prov["location"] = fb.get("location_source"), "manual"

    # AUM: API-derived if available, else human fallback
    if enriched.get("assets"):
        aum_val, aum_source, aum_note = fmt_aum(enriched["assets"]), source_label, None
        prov["aum"] = "api"
    else:
        aum_val, aum_source, aum_note = fb.get("aum"), fb.get("aum_source"), fb.get("aum_note")
        prov["aum"] = "manual" if aum_val else "unavailable"

    prov["classification"] = "human-validated"

    return {
        "entity": d.get("entity"),
        "fo_type": {"value": d.get("fo_type"), "source": d.get("fo_type_source"),
                    "confidence": d.get("record_confidence"), "evidence": d.get("fo_type_evidence")},
        "family": d.get("family"),
        "location": {"city": city, "state": state, "source": loc_source},
        "founded": d.get("founded"),
        "aum": {"value": aum_val, "note": aum_note, "source": aum_source},
        "thesis": {"value": d.get("thesis"), "source": d.get("thesis_source")},
        "decision_makers": d.get("decision_makers") or [],
        "firm_contact": d.get("firm_contact") or {},
        "identifiers": ident,
        "_country": d.get("_country"),
        "discovered_via": d.get("discovered_via"),
        "proof_source": d.get("proof_source"),
        "record_confidence": d.get("record_confidence"),
        "pipeline_provenance": prov,   # which cells were API-derived vs human-validated
    }


def main():
    decisions = json.load(open(DECISIONS, encoding="utf-8"))
    kept = [d for d in decisions if d.get("keep")]
    records = []
    for i, d in enumerate(kept, 1):
        records.append(build_record(d))
        print(f"  [{i}/{len(kept)}] {d.get('entity')}")
        if (d.get("identifiers") or {}).get("ein") or (d.get("identifiers") or {}).get("cik"):
            time.sleep(0.25)  # polite to the APIs
    json.dump(records, open(OUT, "w"), indent=2)
    api = sum(1 for r in records if r["pipeline_provenance"].get("location") == "api"
              or r["pipeline_provenance"].get("aum") == "api")
    print(f"\nProduced {len(records)} records -> family_offices.json")
    print(f"{api} records had at least one field re-derived live from a regulatory API.")


if __name__ == "__main__":
    main()
