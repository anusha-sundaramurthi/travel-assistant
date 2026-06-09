import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST      = os.getenv("QDRANT_HOST")
QDRANT_API_KEY   = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME  = os.getenv("COLLECTION_NAME")

# ── NVIDIA NIM (free tier) ────────────────────────────────
# Sign up at https://build.nvidia.com/ for a free API key
NVIDIA_API_KEY   = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL  = "https://integrate.api.nvidia.com/v1"

# LLM: llama-3.1-8b-instruct (free on NVIDIA NIM)
CHAT_MODEL       = "meta/llama-3.1-8b-instruct"

# Embeddings: NV-Embed-QA (free on NVIDIA NIM, 1024-dim)
EMBEDDING_MODEL  = "nvidia/nv-embedqa-e5-v5"
EMBEDDING_DIM    = 1024

FASTAPI_URL      = "http://localhost:8000"
