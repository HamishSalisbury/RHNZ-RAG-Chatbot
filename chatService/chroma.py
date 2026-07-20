import chromadb
from django.conf import settings

_client = None

def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client

def get_rules_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="rules",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )