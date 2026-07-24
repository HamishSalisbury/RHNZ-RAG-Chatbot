from dataclasses import dataclass, field

import pymupdf as fitz

@dataclass
class ExtractedDocument:
    source: str
    pages: list[tuple[int,str]] = field(default_factory=list)
    images_by_page: dict[int, list[str]] = field(default_factory=dict)

def extract(pdf_path: Path, images_dir: Path) -> ExtractedDocument