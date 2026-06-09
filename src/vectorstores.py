from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from src.config import QDRANT_HOST, QDRANT_API_KEY, COLLECTION_NAME, EMBEDDING_DIM


def get_qdrant_client():
    return QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)


def init_qdrant():
    client = get_qdrant_client()
    existing = [col.name for col in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        print(f"Creating collection '{COLLECTION_NAME}' with dim={EMBEDDING_DIM}...")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
    return client


def clear_qdrant():
    client = get_qdrant_client()
    print(f"[Qdrant] Deleting collection '{COLLECTION_NAME}'...")
    client.delete_collection(collection_name=COLLECTION_NAME)
    print(f"[Qdrant] Recreating collection '{COLLECTION_NAME}'...")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )
    print(f"[Qdrant] Collection cleared and ready.")
    return client
