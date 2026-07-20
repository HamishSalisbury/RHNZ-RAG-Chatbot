import chromadb
from django.conf import settings
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

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

def get_chroma() -> tuple[ClientAPI, Collection]:
    """Return (client, rules_collection) in one call."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="rules",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )
    return client, collection