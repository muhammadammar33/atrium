# Validation Chains — 3 Representative Records

Each record below traces the full chain: **discovery → extraction → enrichment →
validation → confidence → sources.** The three are chosen to show the range of the
pipeline: a clean SEC-sourced office, a clean IRS-990-PF-sourced office, and one
where validation *caught a problem* and deliberately lowered confidence.

---

## Record 1 — Duquesne Family Office LLC  *(SEC trail, high confidence)*

**Discovery source.** SEC EDGAR full-text search (`efts.sec.gov`), filtered to form
**13F-HR** with the query `"family office"`. Surfaced because Duquesne *files* a
13F about itself — the filer *is* the office (identity, not a phrase mention).
CIK 0001536411. *(Script: `discover_family_offices_v2.py`.)*

**Extraction method.** The pipeline parsed the EFTS JSON response, extracting the
filer's display name and CIK from each hit; deduplicated by CIK.

**Enrichment steps.** `build_dataset.py` called the SEC submissions API
(`data.sec.gov/submissions/CIK0001536411.json`) to derive the official name and
business address (New York, NY) live. SEC submissions carry no AUM field, so AUM
fell back to the human-validated range from the proof sources.

**Validation logic.**
1. *Discovery ≠ proof:* classification as a single-family office was confirmed from
   an **independent** source, not the filing — "single-family office of Stanley
   Druckenmiller; accepts no external capital."
2. *Identity:* the 13F filer record confirms it is a real, registered investment
   manager.
3. *AUM:* two sources disagreed (~$4B vs ~$8B), so the value is recorded as a
   **range at medium confidence** rather than false precision.

**Confidence assessment.** Classification **high** (corroborated, independent
sources + SEC filer identity). AUM **medium** (range; sources disagree).

**Exact sources.** Discovery: `efts.sec.gov`. Enrichment: `data.sec.gov` submissions
(CIK 0001536411). Proof: `cnbc.com`, `familyofficehub.io`.

---

## Record 2 — Stanley Family Foundation  *(IRS 990-PF trail, high confidence)*

**Discovery source.** IRS Form **990-PF** trail via the ProPublica Nonprofit
Explorer API; family-foundation query, confirmed as a private foundation via the
filing's form type. EIN 61-0157888. *(Script: `discover_foundations.py`.)*

**Extraction method.** The pipeline parsed the ProPublica search JSON for name, EIN,
city/state, and confirmed `is_private_foundation` from the organization's filing
records.

**Enrichment steps.** `build_dataset.py` called the ProPublica organization API
(`.../organizations/610157888.json`) to derive **total assets (~$554M) directly from
the latest filing**, plus official name and location. Both AUM and location are
API-derived (`pipeline_provenance: api`).

**Validation logic.**
1. *Discovery ≠ proof:* single-family status (Ted & Vada Stanley, est. 1985)
   confirmed from independent sources, not the 990 alone.
2. *Financials:* AUM taken directly from the primary filing data — the
   authoritative source for a foundation's assets.
3. *Scope calibration:* a family foundation is a valid single-family entity per the
   provided sample data (Walton, Emerson Collective).

**Confidence assessment.** **High** — classification from independent sources;
financials from the primary regulatory filing.

**Exact sources.** Discovery + enrichment: ProPublica Nonprofit Explorer (EIN
61-0157888). Proof: `broadinstitute.org`, `insidephilanthropy.com`.

---

## Record 3 — Hao Family Foundation  *(validation caught a problem → low confidence)*

**Discovery source.** IRS 990-PF trail via ProPublica. EIN 47-3853918.
*(Script: `discover_foundations.py`.)*

**Extraction method.** Same ProPublica JSON parse as Record 2.

**Enrichment steps.** `build_dataset.py` attempted an EIN lookup for assets and
location.

**Validation logic — this is where the chain earns its keep.** During the proof
step, the independent source (`altss.com`) **explicitly flagged a name collision**:
"Hao Family Foundation" is easily confused with the **Huo** Family Foundation (UK)
and the **Foundation for Hao-Fountain Syndrome** (a medical nonprofit). Because the
entity's identity could not be cleanly resolved to a single organization from public
sources, the validation logic:
- lowered **classification, location, and AUM to low confidence**;
- recorded AUM as a **range ($188M–$304M)** because sources disagreed;
- attached an explicit note: *verify identity before relying on this record*.

The record was **kept but flagged**, rather than presented as clean or silently
dropped — surfacing the uncertainty instead of hiding it.

**Confidence assessment.** **Low** (deliberate) — identity ambiguity unresolved from
public sources; downstream users are warned.

**Exact sources.** Discovery + enrichment: ProPublica (EIN 47-3853918). Proof:
`altss.com` (which itself surfaced the collision).

---

### Why these three

Record 1 shows the SEC "filer-is-the-entity" discovery principle and live API
enrichment. Record 2 shows the 990-PF trail with financials pulled straight from
the primary filing. Record 3 shows the validation logic doing its real job —
detecting an unresolved identity collision and **downgrading the record honestly**
rather than shipping a clean-looking but unverified row. A dataset is only as
trustworthy as its worst-handled edge case; Record 3 is that edge case, handled.
