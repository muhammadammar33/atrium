import json
from pathlib import Path
from collections import Counter

DATA = Path(__file__).parent / "family_offices.json"


def check_record(r):
    issues = []
    ft = r.get("fo_type") or {}
    if not ft.get("value"):
        issues.append("fo_type.value missing")
    if not ft.get("source"):
        issues.append("fo_type has no source (classification must be proven)")
    if not r.get("discovered_via"):
        issues.append("no discovered_via (how it was found)")
    if not r.get("proof_source"):
        issues.append("no proof_source (independent verification source)")

    fc = r.get("firm_contact") or {}
    has_contact = any(fc.get(k) for k in ("email", "phone", "address", "website", "linkedin"))
    if has_contact and not fc.get("source"):
        issues.append("firm_contact has values but no source (fabrication risk)")

    for dm in r.get("decision_makers") or []:
        if not dm.get("name"):
            issues.append("a decision_maker has no name")
        if (dm.get("work_email") or dm.get("direct_phone")) and not dm.get("source"):
            issues.append(f"decision_maker '{dm.get('name')}' has contact but no source")
    return issues


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    print(f"Dataset: {len(data)} records\n")

    types = Counter((r.get("fo_type") or {}).get("value") for r in data)
    conf = Counter(r.get("record_confidence") for r in data)
    print("By type:", dict(types))
    print("By record confidence:", dict(conf))
    print("-" * 60)

    clean = 0
    for r in data:
        issues = check_record(r)
        if issues:
            print(f"\n! {r.get('entity','(no entity)')}")
            for i in issues:
                print(f"    - {i}")
        else:
            clean += 1
    print("-" * 60)
    print(f"{clean}/{len(data)} records pass the honesty bar.")
    single = types.get("single", 0)
    print(f"Single-family offices: {single}   (target: 50)")


if __name__ == "__main__":
    main()
