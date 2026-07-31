"""CLI entry point for ``python -m ingestion.build_index``."""

import argparse
import logging
import re
import sys
from pathlib import Path
import fitz

from django.utils import text

logger = logging.getLogger("ingestion.build_index")
logging.basicConfig(level=logging.DEBUG)

PARAGRAPH_OVERLAP_TOKENS = 64

def build_index(source: str, output: str, *, force: bool = False) -> None:
    """Build the index.

    TODO: implement. .
    """
    knowledge_files = get_files_to_index(Path(source))
    print(knowledge_files)

    for file in knowledge_files:
        logger.info(f"Indexing file: {file}")
        with fitz.open(file) as f:
            for page_no, page in enumerate(f):
                text = page.get_text("text")
                for paragraph in chunk_paragraphs(text):
                    print(page_no, paragraph)

def get_files_to_index(root: str) -> list[str]:
    """Search the knowledge directory for files to index. Returns a list of file paths."""
    return [str(f) for f in Path(root).rglob("*") if f.is_file()]

def split_with_overlap(text: str, tokenizer, max_tokens: int) -> list[str]:
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    if len(token_ids) <= max_tokens:
        return list[str]

    step = max_tokens - PARAGRAPH_OVERLAP_TOKENS
    pieces = []
    for start in range(0, len(token_ids), step):
        window = token_ids[start : start + max_tokens]
        pieces.append(tokenizer.decode(window).strip())
        if start + max_tokens >= len(token_ids):
            break
    return pieces


def chunk_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

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