import re
from src.embeddings import get_embeddings
from src.config import COLLECTION_NAME
from src.vectorstores import get_qdrant_client

from qdrant_client.models import (
    Prefetch,
    FusionQuery,
    Fusion,
    Document as QdrantDocument,
)


# ── Dynamic threshold ─────────────────────────────────────
# Specific factual queries (elevation, date, permit) need
# tight threshold — we want exact chunk matches.
# Broad queries (itinerary, plan, guide) cast a wider net.

SPECIFIC_KEYWORDS = [
    "elevation", "distance", "year", "age", "how many",
    "when", "who", "permit", "cost", "price", "days",
    "height", "km", "miles", "temperature", "altitude",
    "route", "visa", "document", "passport"
]

BROAD_KEYWORDS = [
    "itinerary", "plan", "guide", "about", "tell me",
    "overview", "describe", "explain", "places", "things to do",
    "what to do", "how to", "help me", "suggest", "recommend",
    "famous", "popular", "best", "top"
]

def get_threshold(query: str) -> float:
    q = query.lower()
    if any(w in q for w in SPECIFIC_KEYWORDS):
        print(f"[Retriever] Specific query detected → threshold 0.55")
        return 0.55
    if any(w in q for w in BROAD_KEYWORDS):
        print(f"[Retriever] Broad query detected → threshold 0.40")
        return 0.40
    print(f"[Retriever] Default threshold → 0.48")
    return 0.48


# ── Query normalizer ──────────────────────────────────────
def normalize_query(query: str) -> str:
    replacements = {
        r'\bsrilanka\b':    'sri lanka',
        r'\bnewzealand\b':  'new zealand',
        r'\bsouthkorea\b':  'south korea',
        r'\bnorthkorea\b':  'north korea',
        r'\bsouthafrica\b': 'south africa',
        r'\bcostariica\b':  'costa rica',
        r'\bcostarica\b':   'costa rica',
        r'\bpuertorico\b':  'puerto rico',
        r'\buae\b':         'united arab emirates',
        r'\busa\b':         'united states',
        r'\buk\b':          'united kingdom',
    }
    normalized = query.lower().strip()
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    if normalized != query.lower().strip():
        print(f"[Retriever] Normalized: '{query}' → '{normalized}'")
    return normalized

def retrieve_docs(query: str, top_k: int = 10, collection_name: str = None) -> list[str]:
    target_collection = collection_name or COLLECTION_NAME
    client            = get_qdrant_client()

    normalized_query      = normalize_query(query)
    TOP_SCORE_THRESHOLD   = get_threshold(normalized_query)
    query_vector          = get_embeddings([normalized_query])[0]

    search_result = client.query_points(
        collection_name=target_collection,
        query=query_vector,
        limit=top_k,
        with_payload=True
    )

    hits = search_result.points

    if not hits:
        print("[Retriever] No results found.")
        return []

    best_score = hits[0].score
    print(f"[Retriever] Best score: {best_score:.3f} | Threshold: {TOP_SCORE_THRESHOLD}")

    if best_score < TOP_SCORE_THRESHOLD:
        print(f"[Retriever] Below threshold — no relevant context")
        return []

    keep_threshold = max(best_score * 0.85, MIN_CHUNK_SCORE)
    relevant       = []

    for hit in hits:
        score  = hit.score
        text   = hit.payload.get("text", "")
        source = hit.payload.get("source", "?")
        if score >= keep_threshold:
            print(f"[Retriever] Kept    {score:.3f} | {source}")
            relevant.append(text)
        else:
            print(f"[Retriever] Dropped {score:.3f} | {source}")

    print(f"[Retriever] Final: {len(relevant)} chunks kept")
    return relevant
