"""CLI entry point for ``python -m ingestion.build_index``."""
import argparse
import logging
import os
import re
import sys
from pathlib import Path
import hashlib
from datetime import datetime, timezone
import fitz
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

from ingestion.errors import MissingEnvVar, KnowledgeDirNotFound

logger = logging.getLogger("ingestion.build_index")

load_dotenv()


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingEnvVar(name=name)
    return value

CHUNKER_VERSION= "1" # Bump when chunking logic changes - forces rebuild
EMBEDDING_MODEL_NAME = require_env("EMBEDDING_MODEL")
MAX_TOKENS = int(require_env("MAX_TOKENS"))
PARAGRAPH_OVERLAP_TOKENS = 64

def build_index(source: str, output: str, *, force: bool = False) -> None:
    """Build the index.

    TODO: implement. .
    """
    root = Path(source)
    if not root.is_dir():
        raise KnowledgeDirNotFound(path=root)

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    tokenizer = model.tokenizer
    knowledge_files = get_files_to_index(Path(source))
    texts, ids, metadatas = [], [], []
    for file in knowledge_files:
        source_name = Path(file).name
        chunk_index = 0

        logger.info(f"Indexing file: {file}")
        with fitz.open(file) as f:
            for page_no, page in enumerate(f):
                text = page.get_text("text")
                for paragraph in chunk_paragraphs(text):
                    for piece in split_with_overlap(paragraph, tokenizer, MAX_TOKENS):
                        texts.append(piece)
                        ids.append(make_chunk_id(source_name, page_no, chunk_index, piece))
                        metadatas.append({
                            "source":source_name,
                            "page":page_no,
                            "chunk_index":chunk_index,
                            "rule_id": "rule" # Rule deriviaton delegated to M2
                        })
                        chunk_index+=1
     
    logger.info("Produced %d chunks", len(texts))

    logger.info("Embedding %d chunks...", len(texts))

    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True # TODO urn of in docker builds 
    )

    client = chromadb.PersistentClient(path=output)

    try:
        client.delete_collection("knowledge")
    except Exception:
        # First ever run - nothing to delete
        pass

    collection = client.create_collection(
        name="knowledge",
        metadata= {
            "source_hash": compute_source_hash(knowledge_files),
            "last_built_at":datetime.now(timezone.utc).isoformat(),
            "chunker_version": CHUNKER_VERSION,
            "embedding_model":EMBEDDING_MODEL_NAME

        }
    )

    for start in range(0, len(ids), 256):
        collection.add(
            ids=ids[start:start+256],
            documents=texts[start:start+256],
            embeddings=embeddings[start:start+256].tolist(),
            metadatas=metadatas[start:start+256]
        )
    logger.info("Stored %d chunks in collection 'knowledge'", collection.count())

    # Embed a test question — must use the same model as the index
    # and the same normalization, or the distances are meaningless
    q = model.encode(["how high can a player hold their stick?"],
                    normalize_embeddings=True)
    # Nearest-neighbour search: return the 3 most similar chunks
    res = collection.query(query_embeddings=q.tolist(), n_results=3)
    # Results are nested per-query: [0] = first query, [0] = its top hit.
    # Should print Article 9's timeout text.
    print(res["documents"][0][0])

def compute_source_hash(files: list[str]) -> str:
    h = hashlib.sha256()

    for f in sorted(files):
        h.update(Path(f).read_bytes())

    h.update(CHUNKER_VERSION.encode())
    h.update(EMBEDDING_MODEL_NAME.encode())

    return h.hexdigest()



def make_chunk_id(source: str, page: int, chunk_index: int, text: str) -> str:
    payload = f"{source}|{page}|{chunk_index}|{text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]

def get_files_to_index(root: str) -> list[str]:
    """Search the knowledge directory for files to index. Returns a list of file paths."""
    return [str(f) for f in Path(root).rglob("*") if f.is_file()]

def split_with_overlap(text: str, tokenizer, max_tokens: int) -> list[str]:
    enc = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = enc["input_ids"], enc["offset_mapping"]
    if len(ids) <= max_tokens:
        return [text]
    step = max_tokens - PARAGRAPH_OVERLAP_TOKENS
    pieces = []
    for start in range(0, len(ids), step):
        end = min(start + max_tokens, len(ids))
        start_char = offsets[start][0]
        end_char = offsets[end - 1][1]
        pieces.append(text[start_char:end_char].strip())
        if end == len(ids):
            break
    return pieces


TOC_LINE = re.compile(r"\.{4,}|…{2,}")   # dotted/ellipsis leaders = table of contents

def chunk_paragraphs(text: str) -> list[str]:
    paragraphs = []
    for p in re.split(r"\n\s*\n", text):
        p = p.replace("\u200b", "").strip()
        if len(p) < 20:              # page numbers, empty/ZWSP-only fragments
            continue
        if TOC_LINE.search(p):       # contents pages
            continue
        paragraphs.append(p)
    return paragraphs

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m ingestion.build_index",
        description="Build the ingestion index.",
    )
    parser.add_argument("--source", default="knowledge", help="Source directory.")
    parser.add_argument("--output", default="index", help="Output directory.")
    parser.add_argument("--force", action="store_true", help="Rebuild even if up to date.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Console entry point. Returns a process exit code."""
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        build_index(args.source, args.output, force=args.force)
    except Exception as exc:  # top-level CLI boundary
        logger.error("Index build failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())