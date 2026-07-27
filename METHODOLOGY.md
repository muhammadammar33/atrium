# Family Office Intelligence — Methodology

## 1. Objective & approach

The goal was to build a decision-grade dataset of family offices and a working
retrieval system on top of it. The dataset was assembled around four principles
that governed every record:

- **Multi-source discovery**, so no single database defines the market.
- **Discovery separated from proof** — the trail that finds an entity is not the
  source used to confirm it.
- **Provenance on every high-value cell** — each classification, figure, and
  contact carries its source.
- **Honest confidence** — uncertainty is recorded, not hidden, and nothing is
  fabricated to make the file look complete.

## 2. Two independent discovery trails

Relying on a single source biases the result toward whatever that source can see.
SEC 13F filings surface only managers above the $100M reporting threshold that are
structured to file — which skews heavily toward multi-family offices and misses
private single-family offices almost entirely. To correct that bias, a second,
independent trail was added: IRS Form 990-PF filings (via ProPublica's Nonprofit
Explorer), which surface the private foundations of wealthy families that the SEC
trail never sees. Two regulatory databases, cross-checked, give a materially less
skewed picture than treating either as the whole market — and directly satisfy the
requirement that the dataset reflect genuine discovery rather than one source
copied at scale.

## 3. Discovery precision: filtering by filing type, not phrase

The first discovery pass searched SEC full-text for the phrase "family office."
Precision was poor — roughly **1 in 75** hits was an actual family office. The
reason is that a phrase search matches *text, not the identity of the filer*:
press releases, prospectuses, and news filings mention "family office" while being
filed by unrelated companies.

The fix was to filter by **13F-HR** filings instead. A 13F is submitted by an
investment manager, about itself, when it manages over $100M. Because firms file
13Fs about themselves, the filer *is* the entity being sought — identity, not
vocabulary. Precision rose dramatically. This is the core discovery principle:
search for the form an entity is *required to file about itself*, not for a phrase
anyone can mention.

## 4. Discovery vs. proof

A discovery hit establishes only that an entity exists and is worth checking — a
13F proves the filer is an investment manager, and a 990-PF proves a foundation
exists, but neither establishes that a firm is a *single*-family office or that a
record's details are current. Each record is therefore confirmed from a **second,
independent source** (the firm's own site, credible news) recorded separately from
the discovery trail.

This separation guards against false positives, same-name collisions, stale data,
and misclassifying a multi-family office or RIA as single-family — failure modes
encountered directly during the build (e.g., the Hao/Huo and Friedman name
collisions, and multi-family firms surfaced by phrase search).

## 5. The single-family invisibility ceiling

The wealthiest single-family offices are the hardest to observe *by design* —
privacy is a feature of how they are structured. They operate through holding
companies, trusts, foundations, LLCs, and external advisers, frequently with no
public website and minimal published staff. This makes thin data a **structural
property of the market, not a research failure**: the more sophisticated the
family, the fewer public signals it leaves.

Even when the family is identifiable, linking it to a specific office, named
decision-maker, or verified contact often requires indirect evidence — and in some
cases the honest, correct result is that the information is simply not publicly
available. Such fields are recorded as blanks rather than fabricated. A practical
consequence: the most prestigious offices tend to have the *lowest* contact
completeness, which is a true signal about the market rather than a gap to paper
over.

## 6. Calibrating the definition of "family office"

The provided sample data (e.g., Walton Family Foundation, Emerson Collective)
revealed that the target definition is broader than a formal investment firm: it
includes family-controlled foundations and mission-driven entities that steward a
family's capital, influence, and long-term interests. The sample was treated as
evidence of intended scope, and inclusion criteria were adjusted accordingly —
admitting foundations and operating entities when they clearly function as part of
a family's broader capital and decision-making structure, rather than excluding
them for not resembling a traditional single-family office.

## 7. Honesty & confidence policy

The governing rule was: **never guess to make the file look complete.** A field was
left blank when it could not be verified; marked low-confidence when some evidence
existed but not enough for certainty; and an entity was excluded entirely when its
identity, family-office role, or relevance could not be confirmed from reliable
sources.

This reflects a deliberate tradeoff: a smaller, trustworthy dataset is more useful
than a fuller-looking one built on assumptions. Blanks and confidence labels make
uncertainty *visible* and actionable, whereas fabricated or weakly-supported values
mislead users and — because trust is not divisible — undermine the credibility of
the entire dataset. A reject/defer log records every excluded entity and the reason
(e.g., professional trustees and licensed trust companies that are not tied to one
family; same-name collisions deferred pending EIN confirmation), as evidence of
evaluation rather than omission.

## 8. Results

- **Records:** 50 verified **single-family offices**. Multi-family offices and
  commercial RIAs surfaced during discovery were evaluated and excluded to the
  reject/defer log (§7), scoping the final dataset to single-family only.
- **Confidence mix:** whole-record — 40 high, 7 medium, 3 low; low-confidence
  records carry explicit notes on what remains unverified.
- **Sources per record:** a discovery trail (SEC 13F-HR / 40-APP, or IRS 990-PF)
  plus a separate proof source; both recorded.
- **Contact completeness:** a minority of records carry publicly-listed contact
  details (firm phone/email from the entity's own site); the remainder honestly
  record contact fields as unavailable, concentrated among the most private offices
  (see §5).
- **Reject/defer log:** maintained separately, with a reason per excluded entity
  (multi-family firms, professional trustees, trust companies, and same-name
  collisions deferred pending EIN confirmation).

## 9. Delivery: the retrieval system

The dataset is delivered through a deployed retrieval-augmented (RAG) search tool,
with the layers kept separate:

- **Data layer** — the structured dataset (`family_offices.json`).
- **Renderer** — turns each record into a searchable text document, converting
  honest blanks into honest statements ("direct contacts not publicly available").
- **Retrieval + grounding** — semantic search with **two grounding controls**: a
  confidence gate in code that declines when nothing is relevant, and an LLM
  instruction that answers only from retrieved records. Verified with queries where
  the code gate passed but the model correctly refused.
- **Interface** — a deployed, public web UI for non-technical users.

## 10. Limitations & next steps

- **Contact validation** — emails are recorded but not yet deliverability-verified;
  a validation pass (syntax, MX, quality scoring) is the next enrichment.
- **Multi-branch families** — entities like the Pritzker family span several
  independent foundations; each recorded branch should have its EIN confirmed.
- **Coverage** — EDGAR skews large; deeper 990-PF paging and additional trails
  (Form ADV, state registries) would extend reach.
- **Recency** — figures are drawn from the latest available filings; a refresh
  cadence would keep AUM and personnel current.
