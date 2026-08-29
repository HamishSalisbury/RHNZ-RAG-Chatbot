"""Query the existing Chroma index without rebuilding it.

Usage (from the project root):
    python -m ingestion.query_index "how many timeouts can each team request"
    python -m ingestion.query_index "what is a direct free hit" --n 5

Loads the persistent Chroma store built by ``python -m ingestion.build_index``,
embeds ONLY the query text, and prints the top-N most similar stored chunks.
The stored chunk embeddings are read as-is; nothing is re-embedded.
"""

import argparse
import sys

import chromadb
from sentence_transformers import SentenceTransformer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ingestion.query_index",
        description="Search the built index for the chunks most similar to a query.",
    )
    parser.add_argument("query", help="The question or text to search for.")
    parser.add_argument("--index", default="index", help="Chroma persist directory (default: index).")
    parser.add_argument("--n", type=int, default=3, help="Number of results to return (default: 3).")
    args = parser.parse_args(argv)

    # Open the existing on-disk store. This does NOT rebuild anything —
    # it just reads what build_index wrote.
    client = chromadb.PersistentClient(path=args.index)
    try:
        collection = client.get_collection("knowledge")
    except Exception:
        print(f"No 'knowledge' collection found in '{args.index}'. "
              f"Run `python -m ingestion.build_index` first.", file=sys.stderr)
        return 1

    # Read the model name from the collection's own freshness metadata.
    # This guarantees the query is embedded by the SAME model that built
    # the index — required for the distances to mean anything (and it is
    # exactly why build_index records `embedding_model` in the metadata).
    meta = collection.metadata or {}
    model_name = meta.get("embedding_model")
    if not model_name:
        print("Collection has no 'embedding_model' metadata; cannot pick a model safely.",
              file=sys.stderr)
        return 1

    print(f"Collection: {collection.count()} chunks | built {meta.get('last_built_at', '?')} "
          f"| model {model_name}")

    model = SentenceTransformer(model_name)

    # Embed only the query — one string, one vector. Normalization must
    # match the build side (unit vectors) or cosine distance misbehaves.
    query_embedding = model.encode([args.query], normalize_embeddings=True)

    res = collection.query(query_embeddings=query_embedding.tolist(), n_results=args.n)

    # Results are nested one level per query; we sent one query, so
    # everything lives at index [0].
    docs = res["documents"][0]
    dists = res["distances"][0]
    metas = res["metadatas"][0]

    for i in range(len(docs)):
        m = metas[i]
        print(f"\n--- result {i}  (distance {dists[i]:.4f})  "
              f"{m.get('source', '?')} page {m.get('page', '?')}  "
              f"chunk {m.get('chunk_index', '?')} ---")
        print(docs[i])

    return 0


if __name__ == "__main__":
    sys.exit(main())