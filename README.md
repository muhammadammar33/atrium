# Atrium

Retrieval-augmented family-office intelligence search. Ask plain-language
questions over a verified dataset; answers cite source records, and the system
declines when evidence is weak.

**Live demo:** _https://your-app.streamlit.app_

## Architecture

```
family_offices.json  →  records.py  →  engine.py  →  streamlit_app.py
     (data)              (renderer)    (RAG)           (UI)
```

- **Data** — `family_offices.json` stores structured records with per-cell
  provenance and confidence.
- **Renderer** — `records.py` turns each record into a searchable text document
  for embedding.
- **Engine** — `engine.py` retrieves top matches, then applies two grounding
  controls: a confidence gate in code (decline below threshold) and an LLM
  instruction to answer only from the retrieved records.
- **UI** — `streamlit_app.py` presents answers, declines, and source cards.

## Data pipeline

Standalone scripts under `pipeline/` build and verify the dataset:

1. **Discovery** — SEC EDGAR full-text search (forms a family office files) and
   IRS 990-PF private foundations via ProPublica.
2. **Verification** — confirm each candidate from a second independent source;
   enrichment pulls official EDGAR submissions.
3. **Dataset** — curated records land in `family_offices.json` with provenance.

Discovery is not proof: a filing mention or foundation lead does not by itself
confirm a family office.

## Run locally

```bash
pip install -r requirements.txt
set GROQ_API_KEY=your_key_here   # PowerShell: $env:GROQ_API_KEY = "..."
streamlit run streamlit_app.py
```

On Streamlit Cloud, set `GROQ_API_KEY` in app secrets.
