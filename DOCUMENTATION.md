# Documentation Note: Atrium Family Office Intelligence (RAG)

## Stack choices

- **Language:** Python.
- **Data pipeline:** `requests` against two free, official APIs, SEC EDGAR
  (full-text search + submissions) and IRS 990-PF via ProPublica Nonprofit
  Explorer. No paid data sources.
- **Dataset:** `family_offices.json` (structured records with per-cell provenance),
  emitted by `build_dataset.py` from a human judgment layer (`decisions.json`) plus
  live API enrichment.
- **Embeddings / retrieval:** `sentence-transformers` (local) + `scikit-learn`
  cosine similarity.
- **Generation:** Groq API, `llama-3.1-8b-instant` (free tier).
- **Interface / hosting:** Streamlit, deployed on Streamlit Community Cloud (public
  URL). Chosen over a FastAPI + separate frontend after Hugging Face Docker moved to
  paid, Streamlit gives one free deploy that handles the ML dependencies and
  produces a customer-facing UI (not a raw API/console).

## Chunking strategy

**Record-level chunking, one document per family office.** Each record is rendered
(`records.py`) into a single, self-contained text document. Records are short and
entity-scoped, so sub-chunking would fragment an office across vectors and hurt
retrieval; keeping one chunk per entity means a query returns whole offices, which
is what a user wants. The renderer also converts honest blanks into honest
statements (e.g., "direct contacts not publicly available") so the model can state
gaps truthfully.

## Embedding model

`all-mpnet-base-v2`. Started with `all-MiniLM-L6-v2` (smaller/faster) but switched
after testing: mpnet gave stronger semantic matching. Documented tradeoff, larger
model, slower per query, ~420MB, accepted for accuracy on this small corpus.

## Retrieval approach

Semantic search: embed the query, cosine-similarity against record embeddings,
take top-k = 3. **Two independent grounding controls:**
1. **Code-level confidence gate**: if the top similarity is below a threshold, the
   system declines *before* the LLM is called (structural, not a prompt).
2. **LLM grounding instruction**: the model answers *only* from retrieved records
   and states when they don't support an answer.
Verified with queries where the gate passed but the model still correctly refused,
confirming the LLM control is the load-bearing guarantee.

## What works (live queries I ran on the deployed system)

- **"Which family offices focus on medical research?"** → correctly returned Stanley
  and Baustert as strong matches (0.53, 0.51) with source records. Correct retrieval
  + grounded answer.
- **"Who runs the Crown family office?"** → returned Steve Crown (Exec Chairman) and
  Bill Crown (President & CEO), drawn only from the record. Correct.
- **Out-of-scope queries** (e.g., crypto) → the system declined rather than
  fabricating. Grounding holds.

## What does not work (and how I found it)

- **"single-family offices in Chicago"** → returned SFO-flavored records from *other*
  cities (Crabill/SF, Karsh/LA, Hall/KC) and missed the Chicago offices actually in
  the dataset (Crown, Zell, Steans, Hunter). **Root cause:** retrieval is purely
  semantic and *not field-aware*, the phrase "single-family office" dominates the
  similarity and the city constraint is ignored. Notably, the grounding control
  behaved correctly and did **not** invent a Chicago office; it said it had no match.
- **Threshold is coarse**: a single global similarity cutoff can't cleanly separate
  borderline queries; the LLM-level control does the real grounding work.

## What I would improve

1. **Hybrid retrieval**: combine a structured filter (city/state, AUM band, sector)
   with semantic ranking, so attribute-specific queries (like Chicago) return the
   right records while still ranking by relevance. This is the single highest-impact
   fix.
2. **Contact validation**: add email deliverability checks (syntax, MX, quality
   scoring) to populate the email-validation columns in the target schema.
3. **Threshold/reranking**: replace the fixed cutoff with a reranking step or a
   per-model calibrated threshold.
4. **Coverage & recency**: deeper 990-PF paging, add Form ADV and state registries,
   and a refresh cadence to keep AUM and personnel current.
