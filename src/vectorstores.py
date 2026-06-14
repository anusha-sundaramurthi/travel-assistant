from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from src.config import QDRANT_HOST, QDRANT_API_KEY, COLLECTION_NAME


def get_qdrant_client():
    return QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)


def _ensure_collection(client: QdrantClient, collection_name: str):
    """Create collection if it doesn't exist."""
    existing = [col.name for col in client.get_collections().collections]
    if collection_name not in existing:
        print(f"[Qdrant] Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        print(f"[Qdrant] Collection '{collection_name}' created.")


def init_qdrant(collection_name: str = None):
    """Initialize default or specific collection."""
    client = get_qdrant_client()
    name = collection_name or COLLECTION_NAME
    _ensure_collection(client, name)
    print(f"Database initialization complete for '{name}'.")
    return client


def init_bot_collection(bot_id: str):
    """Create a dedicated Qdrant collection for a bot."""
    client = get_qdrant_client()
    _ensure_collection(client, bot_id)
    return client


def clear_qdrant(collection_name: str = None):
    """Wipe and recreate a collection."""
    client  = get_qdrant_client()
    name    = collection_name or COLLECTION_NAME
    print(f"[Qdrant] Deleting collection '{name}'...")
    client.delete_collection(collection_name=name)
    print(f"[Qdrant] Recreating collection '{name}'...")
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    print(f"[Qdrant] Collection '{name}' cleared and ready.")
    return client


def delete_collection(collection_name: str):
    """Fully delete a collection (used when bot is deleted)."""
    client = get_qdrant_client()
    existing = [col.name for col in client.get_collections().collections]
    if collection_name in existing:
        client.delete_collection(collection_name=collection_name)
        print(f"[Qdrant] Collection '{collection_name}' deleted.")