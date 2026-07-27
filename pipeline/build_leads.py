import json, re
from pathlib import Path

def load(p):
    try: return json.load(open(p))
    except Exception: return []

def family_hint(name):
    return re.sub(r'\s*(family )?(foundation|trust)\s*$', '', name or '', flags=re.I).strip() or name

def build():
    leads = []
    for c in load('verified_candidates.json'):
        if (c.get('signal') or '').startswith('strong'):
            leads.append({
                "name": c.get('official_name') or c.get('entity'),
                "cik": c.get('cik'), "website": None,
                "discovered_via": c.get('discovered_via'),
                "_from": "edgar", "_loc": f"{c.get('city')}, {c.get('state')}",
            })
    fnd = [x for x in load('foundation_leads.json')
           if x.get('is_private_foundation')
           and (x.get('name') or '').strip().lower() not in ('family foundation', 'family trust')]
    fnd.sort(key=lambda x: (x.get('assets') or 0), reverse=True)
    for x in fnd:
        leads.append({
            "name": x.get('name'), "ein": str(x.get('ein')), "website": None,
            "discovered_via": x.get('discovered_via'),
            "_from": "990pf", "_family_hint": family_hint(x.get('name')),
            "_assets_musd": round((x.get('assets') or 0)/1e6), "_loc": f"{x.get('city')}, {x.get('state')}",
        })
    return leads

if __name__ == "__main__":
    leads = build()
    json.dump(leads, open('leads_to_enrich.json', 'w'), indent=2)
    edgar = sum(1 for l in leads if l['_from']=='edgar')
    pf = sum(1 for l in leads if l['_from']=='990pf')
    print(f"{len(leads)} leads written to leads_to_enrich.json  ({edgar} from EDGAR, {pf} from 990-PF)")
