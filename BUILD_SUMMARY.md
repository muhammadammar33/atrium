# Build Session Summary

**Approximate build time:** ~28 hours
over 2 days.

**Main work sessions:**
- *Session 1:* built the RAG system: retrieval engine, grounding controls, and the
  deployed Streamlit app.
- *Session 2:* discovery + enrichment pipeline (SEC EDGAR 13F, IRS 990-PF via
  ProPublica) and dataset construction to 50 records.
- *Session 3:* formalized the build pipeline (decisions layer + programmatic
  assembly), wrote the methodology, validation chains, and documentation.

**Major components, what AI produced vs. what I decided/changed:**

This was heavily AI-assisted, and I'm reporting that plainly.

- **Pipeline & app code** (discovery, enrichment, RAG engine, Streamlit UI,
  exporter, `build_dataset.py`): AI-generated. I directed the architecture
  decisions, two-source discovery, single-family scope, record-level chunking,
  the two-control grounding design, ran and tested everything, configured and
  debugged the deployment, and can explain each component.
- **Dataset (50 records):** AI drafted record JSON from sources I retrieved; I made
  the single-vs-multi classification calls, caught duplicates (e.g., Sobrato
  philanthropy arm, Jeffrey management entity) and name collisions (Hao/Huo,
  Friedman, Phillips, Pritzker branches), deferred entities I couldn't verify, and
  set the scope. Location and AUM are re-derived programmatically from regulatory
  APIs by the pipeline; classification and proof sourcing were human judgment calls.
- **Methodology & documentation:** the core reasoning sections (discovery precision,
  discovery-vs-proof, the single-family invisibility finding, definition
  calibration, honesty policy, and the retrieval limitation I found live) are my own
  analysis, written up with AI help on structure and wording.
- **AI tools used:** Claude. Every high-value cell was checked against a
  primary or independent secondary source; blanks were left rather than guessed;
  nothing was fabricated.
