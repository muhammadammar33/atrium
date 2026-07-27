# Atrium

Retrieval-augmented family-office intelligence search over a verified
50-record single-family-office dataset. Answers cite source records; the
system declines when evidence is weak.

**Live demo:** _https://your-app.streamlit.app_

## Architecture

```
family_offices.json  →  records.py  →  engine.py  →  streamlit_app.py
     (data)              (renderer)    (RAG)           (UI)
```

- **Data** — `family_offices.json`: 50 single-family offices with per-cell
  provenance and confidence. See `METHODOLOGY.md` for how the dataset was built.
- **Renderer** — `records.py` turns each record into a searchable text document.
- **Engine** — `engine.py` retrieves top matches, then applies two grounding
  controls: a confidence gate in code (decline below threshold) and an LLM
  instruction to answer only from the retrieved records.
- **UI** — `streamlit_app.py` presents answers, declines, and source cards.

Dataset tools at the repo root (operate on files beside them):
`validate_dataset.py`, `export_to_xlsx.py`, `record_template.json`,
`rejected_leads.json`, `family_offices_export.xlsx`.

## Data pipeline

Scripts and intermediate JSON live under `pipeline/`:

1. **Discovery** — SEC EDGAR full-text search (forms a family office files) and
   IRS 990-PF private foundations via ProPublica.
2. **Verification / enrichment** — confirm candidates from a second independent
   source; assemble leads and fetch draft evidence (`build_leads.py`,
   `enrich_lead.py`, `verify_candidates.py`).
3. **Dataset** — curated records in `family_offices.json` with provenance and
   confidence; rejections tracked in `rejected_leads.json`.

Discovery is not proof: a filing mention or foundation lead does not by itself
confirm a family office.

## Run locally

```bash
pip install -r requirements.txt
set GROQ_API_KEY=your_key_here   # PowerShell: $env:GROQ_API_KEY = "..."
streamlit run streamlit_app.py
```

On Streamlit Cloud, set `GROQ_API_KEY` in app secrets. Run pipeline scripts from
inside `pipeline/` so their relative JSON paths resolve correctly.
