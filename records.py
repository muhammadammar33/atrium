import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "family_offices.json"


def load_records():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _val(cell):
    """A cell may be a {'value': ...} dict or a plain scalar."""
    if isinstance(cell, dict):
        return cell.get("value")
    return cell


def to_document(r):
    """Render one structured record into a searchable text paragraph."""
    parts = []

    name = r["entity"]
    fo = _val(r.get("fo_type")) or "family"
    loc = r.get("location") or {}
    where = f"in {loc['city']}, {loc['state']}" if loc.get("city") else ""
    intro = f"{name} is a {fo}-family office {where}".strip()

    fam = r.get("family")
    if fam:
        intro += f", serving the {fam} family" if "family" not in fam.lower() else f", serving the {fam}"

    extras = []
    if _val(r.get("founded")):
        extras.append(f"founded {_val(r['founded'])}")
    hc = _val(r.get("headcount"))
    if hc:
        hc = str(hc)
        already = any(w in hc.lower() for w in ("staff", "professional", "employee", "people"))
        extras.append(hc if already else f"{hc} staff")
    if extras:
        intro += f" ({', '.join(extras)})"
    parts.append(intro.rstrip() + ".")

    if _val(r.get("thesis")):
        parts.append(f"Investment focus: {_val(r['thesis'])}.")

    aum = r.get("aum") or {}
    if _val(aum):
        parts.append(f"Estimated AUM: {_val(aum)}.")
    elif aum.get("note"):
        parts.append(f"AUM {aum['note']}.")

    dms = r.get("decision_makers") or []
    if dms:
        names = "; ".join(
            f"{d['name']} ({d['title']})" if d.get("title") else d["name"]
            for d in dms
        )
        parts.append(f"Key decision-makers: {names}.")

    fc = r.get("firm_contact") or {}
    cbits = []
    if fc.get("phone"):
        cbits.append(f"phone {fc['phone']}")
    if fc.get("email"):
        cbits.append(f"email {fc['email']}")
    if fc.get("website"):
        cbits.append(f"website {fc['website']}")
    if fc.get("address"):
        cbits.append(fc["address"])
    if cbits:
        parts.append("Firm contact: " + "; ".join(cbits) + ".")

    if dms and all(not d.get("work_email") and not d.get("direct_phone") for d in dms):
        parts.append("Direct contact details for individual decision-makers "
                     "are not publicly available.")

    return " ".join(parts)


def load_documents():
    """Return [{'text': <searchable paragraph>, 'record': <structured dict>}]."""
    return [{"text": to_document(r), "record": r} for r in load_records()]


if __name__ == "__main__":
    for d in load_documents():
        print("-" * 78)
        print(d["text"])
