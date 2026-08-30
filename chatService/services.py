import os
import chromadb
from sentence_transformers import SentenceTransformer
import sys
from config.settings import RULES_TOP_K
from config.settings import PATH_TO_INDEX
from config.settings import MIN_COSINE_SIMILIARITY
def query_chatbot(query):

    client = chromadb.PersistentClient(path=PATH_TO_INDEX)
    try:
        collection = client.get_collection("knowledge")
    except Exception:
        print(f"No 'knowledge' collection found in '{PATH_TO_INDEX}'. "
              f"Run `python -m ingestion.build_index` first.", file=sys.stderr)
        return 1

    meta = collection.metadata or {}
    model_name = meta.get("embedding_model")
    if not model_name:
        print("Collection has no embedding model metadata; cannot pick a model safely", file = sys.stderr)
        return 1

    model = SentenceTransformer(model_name)

    query_embedding = model.encode([query], normalize_embeddings=True)

    res = collection.query(query_embeddings=query_embedding.tolist(), n_results=RULES_TOP_K)
    docs = res["documents"][0]
    dists = res["distances"][0]
    metas = res["metadatas"][0]

    keep = [i for i, dist in enumerate(dists) if (1 - dist) >= MIN_COSINE_SIMILIARITY]

    res["documents"][0] = [docs[i] for i in keep]
    res["distances"][0] = [dists[i] for i in keep]
    res["metadatas"][0] = [metas[i] for i in keep]

    return res  

