import re
from src.embeddings import get_embeddings
from src.config import COLLECTION_NAME
from src.vectorstores import get_qdrant_client


# ── Thresholds ────────────────────────────────────────────
# These are domain-agnostic — they work the same regardless
# of how many PDFs or topics are in the collection.
#
# ABSOLUTE_FLOOR: no chunk below this score is ever kept,
#                 no matter what.
# RELATIVE_KEEP:  chunks within this fraction of the best
#                 score are kept alongside it (catches
#                 multiple relevant chunks, not just #1).
ABSOLUTE_FLOOR     = 0.30
RELATIVE_KEEP      = 0.80   # keep chunks scoring >= 80% of best score
MIN_RESULTS_WANTED = 3      # try to return at least this many chunks if available


def normalize_query(query: str) -> str:
    """
    Generic, domain-agnostic normalisation.

    Only expands UNAMBIGUOUS acronyms — ones that have no
    common-English collision risk. Removed risky short forms
    (ui, ux, db, nw) that could misfire inside PDFs unrelated
    to tech, since this collection now spans 13+ domains.
    Safe to extend, but keep entries conservative.
    """
    replacements = {
        r'\bai\b':    'artificial intelligence',
        r'\bml\b':    'machine learning',
        r'\bdsa\b':   'data structures and algorithms',
        r'\biot\b':   'internet of things',
        r'\bnlp\b':   'natural language processing',
        r'\busa\b':   'united states',
        r'\buk\b':    'united kingdom',
        r'\buae\b':   'united arab emirates',
    }
    normalized = query.lower().strip()
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    if normalized != query.lower().strip():
        print(f"[Retriever] Normalized: '{query}' -> '{normalized}'")
    return normalized


def retrieve_docs(query: str, top_k: int = 15, collection_name: str = None) -> list[str]:
    """
    Domain-agnostic semantic retrieval.

    Works the same way regardless of how many PDFs / topics
    are in the collection — no keyword lists to maintain.

    Strategy:
    1. Embed the query, search top_k candidates.
    2. If nothing clears the absolute floor, return nothing
       (genuinely no relevant info exists).
    3. Otherwise keep every chunk within RELATIVE_KEEP of the
       best score — this naturally adapts: a very confident
       top match keeps a tight set, a fuzzy match keeps a
       wider net automatically.
    4. Always try to return at least MIN_RESULTS_WANTED chunks
       if the absolute floor allows it, so partial/related
       content still reaches the LLM instead of an empty list.
    5. Final list is always returned sorted best-score-first,
       regardless of whether chunks came from the primary
       pass or the fallback pass.
    """
    target_collection = collection_name or COLLECTION_NAME
    client             = get_qdrant_client()

    normalized_query = normalize_query(query)
    query_vector     = get_embeddings([normalized_query])[0]

    search_result = client.query_points(
        collection_name=target_collection,
        query=query_vector,
        limit=top_k,
        with_payload=True
    )

    hits = search_result.points

    if not hits:
        print("[Retriever] No results found in collection.")
        return []

    best_score = hits[0].score
    print(f"[Retriever] Best score: {best_score:.3f} | Absolute floor: {ABSOLUTE_FLOOR}")

    if best_score < ABSOLUTE_FLOOR:
        print(f"[Retriever] Best score below absolute floor — no relevant context exists")
        return []

    # Relative threshold scales with how confident the best match is
    keep_threshold = max(best_score * RELATIVE_KEEP, ABSOLUTE_FLOOR)

    scored_relevant = []   # (score, text, source) — passed relative threshold
    scored_fallback = []   # (score, text, source) — between floor and threshold

    for hit in hits:
        score  = hit.score
        text   = hit.payload.get("text", "")
        source = hit.payload.get("source", "?")
        if score >= keep_threshold:
            scored_relevant.append((score, text, source))
        elif score >= ABSOLUTE_FLOOR:
            scored_fallback.append((score, text, source))
        # else: below absolute floor, always discarded

    for score, text, source in scored_relevant:
        print(f"[Retriever] Kept     {score:.3f} | {source}")

    # If we don't have enough confident chunks, pull in the
    # next-best fallback chunks (still above absolute floor)
    # so the LLM has more to work with on fuzzy/broad queries.
    if len(scored_relevant) < MIN_RESULTS_WANTED and scored_fallback:
        needed = MIN_RESULTS_WANTED - len(scored_relevant)
        scored_fallback.sort(key=lambda x: x[0], reverse=True)
        for score, text, source in scored_fallback[:needed]:
            print(f"[Retriever] Fallback {score:.3f} | {source}")
            scored_relevant.append((score, text, source))

    # Always return best-score-first, regardless of which pass
    # a chunk came from — keeps context ordering consistent
    # for the LLM (strongest evidence first).
    scored_relevant.sort(key=lambda x: x[0], reverse=True)
    relevant = [text for _, text, _ in scored_relevant]

    print(f"[Retriever] Final: {len(relevant)} chunks kept")
    return relevant
