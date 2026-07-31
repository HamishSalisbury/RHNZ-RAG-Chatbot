"""CLI entry point for ``python -m ingestion.build_index``."""
import argparse
import logging
import os
import re
import sys
from pathlib import Path

import fitz
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from ingestion.errors import MissingEnvVar, KnowledgeDirNotFound

logger = logging.getLogger("ingestion.build_index")

load_dotenv()


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingEnvVar(name=name)
    return value


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
    print(knowledge_files)

    for file in knowledge_files:
        logger.info(f"Indexing file: {file}")
        with fitz.open(file) as f:
            for page_no, page in enumerate(f):
                text = page.get_text("text")
                for paragraph in chunk_paragraphs(text):
                    for piece in split_with_overlap(paragraph, tokenizer, MAX_TOKENS):
                        print("-----")
                        print(repr(piece))

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
    parser.add_argument("--source", default="data", help="Source directory.")
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