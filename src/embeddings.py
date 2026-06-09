from openai import OpenAI
from src.config import NVIDIA_API_KEY, NVIDIA_BASE_URL, EMBEDDING_MODEL

client = OpenAI(
    api_key=NVIDIA_API_KEY,
    base_url=NVIDIA_BASE_URL
)

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Uses NVIDIA NIM's nv-embedqa-e5-v5 model (free tier).
    The model returns 1024-dim vectors.
    input_type must be 'query' for retrieval queries and
    'passage' for documents being indexed.
    """
    response = client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
        encoding_format="float",
        extra_body={"input_type": "passage", "truncate": "END"}
    )
    return [item.embedding for item in response.data]


def get_query_embedding(query: str) -> list[float]:
    """Embed a retrieval query (uses input_type='query')."""
    response = client.embeddings.create(
        input=[query],
        model=EMBEDDING_MODEL,
        encoding_format="float",
        extra_body={"input_type": "query", "truncate": "END"}
    )
    return response.data[0].embedding
