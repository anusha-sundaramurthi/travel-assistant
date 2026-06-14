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
from sentence_transformers import CrossEncoder


# ── Reranker (loaded once, reused across requests) ────────
_reranker = None

def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        print("[Reranker] Loading cross-encoder model...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        print("[Reranker] Model loaded.")
    return _reranker


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


# ── Reranker ──────────────────────────────────────────────
def rerank(query: str, chunks: list[str], top_n: int = 4) -> list[str]:
    if not chunks:
        return chunks
    if len(chunks) == 1:
        return chunks

    reranker = get_reranker()
    pairs  = [(query, chunk) for chunk in chunks]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)

    print(f"[Reranker] Scores: {[round(s, 3) for s, _ in ranked]}")
    print(f"[Reranker] Kept top {min(top_n, len(ranked))} chunks")

    return [chunk for _, chunk in ranked[:top_n]]


# ── Main retrieval function ───────────────────────────────
def retrieve_docs(query: str, top_k: int = 15) -> list[str]:
    """
    Hybrid retrieval pipeline:
    1. Normalize query spelling
    2. Dynamic threshold based on query type
    3. Hybrid search — dense (OpenAI ada-002) + sparse (BM25)
       fused with Reciprocal Rank Fusion (RRF)
    4. Score threshold filtering
    5. Reranking with cross-encoder to pick best 4 chunks
    """
    client = get_qdrant_client()

    # Step 1 — normalize
    normalized_query = normalize_query(query)

    # Step 2 — dynamic threshold
    TOP_SCORE_THRESHOLD = get_threshold(normalized_query)

    # Step 3 — embed query for dense search
    query_vector = get_embeddings([normalized_query])[0]

    # Step 4 — hybrid search (dense + BM25 fused via RRF)
    # Fetch top 20 from each, fuse, return top_k
    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(
                query=query_vector,
                using="dense",
                limit=20
            ),
            Prefetch(
                query=QdrantDocument(
                    text=normalized_query,
                    model="Qdrant/bm25"
                ),
                using="bm25",
                limit=20
            )
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
        with_payload=True
    )

    hits = search_result.points

    if not hits:
        print("[Retriever] No results found in Qdrant.")
        return []

    # Step 5 — score threshold check
    best_score = hits[0].score
    print(f"[Retriever] Best RRF score: {best_score:.3f} | Threshold: {TOP_SCORE_THRESHOLD}")

    if best_score < TOP_SCORE_THRESHOLD:
        print(f"[Retriever] Best score below threshold — no relevant context")
        return []

    # Step 6 — relative + absolute filter
    keep_threshold = max(best_score * 0.80, TOP_SCORE_THRESHOLD)

    relevant = []
    for hit in hits:
        score  = hit.score
        text   = hit.payload.get("text", "")
        source = hit.payload.get("source", "?")
        if score >= keep_threshold:
            print(f"[Retriever] Kept    {score:.3f} | {source}")
            relevant.append(text)
        else:
            print(f"[Retriever] Dropped {score:.3f} | {source}")

    print(f"[Retriever] After threshold: {len(relevant)} chunks")

    if not relevant:
        return []

    # Step 7 — rerank and return best 4
    reranked = rerank(normalized_query, relevant, top_n=4)
    print(f"[Retriever] Final: {len(reranked)} chunks after reranking")
    return reranked
