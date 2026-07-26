"""CLI entry point for ``python -m ingestion.build_index``."""

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger("ingestion.build_index")
logging.basicConfig(level=logging.DEBUG)

def build_index(source: str, output: str, *, force: bool = False) -> None:
    """Build the index.

    TODO: implement. .
    """
    print(get_files_to_index(Path(source)))

def get_files_to_index(root: str) -> list[str]:
    """Search the knowledge directory for files to index. Returns a list of file paths."""
    return [str(f) for f in Path(root).rglob("*") if f.is_file()]

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