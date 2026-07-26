"""
engine.py  --  the RAG engine (retrieval + grounding control + generation).

Layers kept separate on purpose: this is the "brain", app.py is the web
layer, index.html is the interface. The embedding model loads lazily on the
first search so the server starts fast.
"""

import os
from sklearn.metrics.pairwise import cosine_similarity

EMBED_MODEL = "all-mpnet-base-v2"   # stronger model (accuracy over speed/size)
LLM_MODEL = "llama-3.1-8b-instant"
CONFIDENCE_THRESHOLD = 0.29         # coarse pre-filter; the LLM control is the real guard
TOP_K = 3

# --- DATA LAYER (temporary: later replaced by your real pipeline's output) ---
RECORDS = [
    "Cascade Peak Holdings is a single-family office in Seattle managing the "
    "wealth of a technology founder. Focus: early-stage biotech and life "
    "sciences venture investments.",
    "Harbor Line Capital is a multi-family office in Boston serving twelve "
    "families. Focus: public equities, municipal bonds, and real estate.",
    "Fenwick Trust is a single-family office in London. Focus: sustainable "
    "agriculture, farmland, and clean-energy infrastructure projects.",
    "Meridian Family Advisors is a multi-family office in New York offering "
    "tax, estate planning, and philanthropy services to wealthy families.",
    "Rowan Ridge Office is a single-family office in Austin backed by an "
    "oil-and-gas fortune. Focus: healthcare startups and medical devices.",
]

_embedder = None
_record_embeddings = None


def _ensure_ready():
    global _embedder, _record_embeddings
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL)
        _record_embeddings = _embedder.encode(RECORDS)


# --- RETRIEVAL LAYER ---
def retrieve(question, top_k=TOP_K):
    _ensure_ready()
    q_emb = _embedder.encode([question])
    scores = cosine_similarity(q_emb, _record_embeddings)[0]
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return [{"text": RECORDS[i], "score": float(s)} for i, s in ranked[:top_k]]


# --- GROUNDING CONTROL + GENERATION LAYER ---
SYSTEM_PROMPT = (
    "You are a family-office intelligence assistant for investment "
    "professionals. Answer ONLY using the records provided in the user "
    "message. Do not use outside knowledge. Name the specific family "
    "office(s) your answer draws on. Keep the answer concise and factual. "
    "If the records don't contain enough to answer, say so plainly."
)


def answer_question(question):
    """Return a dict: {answered, best_score, text, sources}."""
    sources = retrieve(question)
    best_score = sources[0]["score"] if sources else 0.0

    # CONTROL 1 (code): refuse when nothing is even close.
    if best_score < CONFIDENCE_THRESHOLD:
        return {
            "answered": False,
            "best_score": best_score,
            "text": ("There isn't strong enough evidence in the current "
                     "dataset to answer this confidently. The closest records "
                     "are shown below, but none is a solid match."),
            "sources": sources,
        }

    # Graceful failure if the key isn't configured (avoids an ugly 500).
    if "GROQ_API_KEY" not in os.environ:
        return {
            "answered": False,
            "best_score": best_score,
            "text": "The answer service isn't configured yet (missing API key).",
            "sources": sources,
        }

    context = "\n\n".join(
        f"RECORD {i+1}: {s['text']}" for i, s in enumerate(sources)
    )
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    completion = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",
             "content": f"RECORDS:\n{context}\n\nQUESTION: {question}"},
        ],
    )
    return {
        "answered": True,
        "best_score": best_score,
        "text": completion.choices[0].message.content.strip(),
        "sources": sources,
    }
