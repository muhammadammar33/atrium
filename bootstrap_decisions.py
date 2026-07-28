import json
from pathlib import Path

SRC = Path(__file__).parent / "family_offices.json"
OUT = Path(__file__).parent / "decisions.json"


def val(cell):
    return cell.get("value") if isinstance(cell, dict) else cell


def to_decision(r):
    ft = r.get("fo_type") or {}
    loc = r.get("location") or {}
    aum = r.get("aum") or {}
    thesis = r.get("thesis") or {}
    return {
        "entity": r.get("entity"),
        "keep": True,
        # --- human judgment (permitted) ---
        "fo_type": val(ft),
        "fo_type_source": ft.get("source"),
        "fo_type_evidence": ft.get("evidence"),
        "family": r.get("family"),
        "identifiers": r.get("identifiers") or {"cik": None, "ein": None},
        "thesis": val(thesis),
        "thesis_source": thesis.get("source"),
        "founded": r.get("founded"),
        "decision_makers": r.get("decision_makers") or [],
        "firm_contact": r.get("firm_contact") or {},
        "discovered_via": r.get("discovered_via"),
        "proof_source": r.get("proof_source"),
        "record_confidence": r.get("record_confidence"),
        "_country": r.get("_country"),
        # --- values the pipeline will try to re-derive from APIs; used only as fallback ---
        "manual_fallback": {
            "official_name": r.get("entity"),
            "city": loc.get("city"),
            "state": loc.get("state"),
            "location_source": loc.get("source"),
            "aum": val(aum),
            "aum_note": aum.get("note"),
            "aum_source": aum.get("source"),
        },
    }


if __name__ == "__main__":
    records = json.load(open(SRC, encoding="utf-8"))
    decisions = [to_decision(r) for r in records]
    json.dump(decisions, open(OUT, "w"), indent=2)
    print(f"Wrote {len(decisions)} decisions to decisions.json "
          f"(your judgment layer). Review it, then run build_dataset.py.")
