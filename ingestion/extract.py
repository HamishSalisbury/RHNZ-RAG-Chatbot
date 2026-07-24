from dataclasses import dataclass, field
from pathlib import Path

import pymupdf as fitz

@dataclass
class ExtractedDocument:
    source: str
    pages: list[tuple[int,str]] = field(default_factory=list)
    images_by_page: dict[int, list[str]] = field(default_factory=dict)

_MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _MODULE_DIR.parents[0]        # module lives at <root>/<pkg>/extract.py
DEFAULT_IMAGES_DIR = PROJECT_ROOT / "out" / "images"


def extract(pdf_path: Path, images_dir: Path = DEFAULT_IMAGES_DIR) -> ExtractedDocument:
    """Extract text per page and write images to images_dir.
    """
    if not images_dir.is_absolute():
        raise ValueError(
            f"images_dir must be an absolute path, got {str(images_dir)!r}. "
            f"Use Path.resolve() at the call site if it comes from a CLI arg."
        )
    images_dir.mkdir(parents=True, exist_ok=True)
    ...