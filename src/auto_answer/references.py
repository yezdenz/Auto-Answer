"""Safe, bounded extraction of local PDF reference material."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MAX_PDF_FILES = 8
MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_REFERENCE_CHARS = 80_000
MAX_PAGES_PER_FILE = 500


@dataclass(frozen=True)
class ReferenceLoadResult:
    context: str
    paths: tuple[str, ...]
    document_count: int
    page_count: int
    character_count: int
    warnings: tuple[str, ...] = ()


def build_reference_context(documents: Iterable[tuple[str, str]]) -> str:
    """Build a bounded prompt section from ``(name, extracted_text)`` pairs."""
    remaining = MAX_REFERENCE_CHARS
    sections: list[str] = []
    for name, raw_text in documents:
        text = "\n".join(line.rstrip() for line in raw_text.splitlines()).strip()
        if not text or remaining <= 0:
            continue
        header = f"\n--- REFERENCE: {name} ---\n"
        allowance = max(0, remaining - len(header))
        excerpt = text[:allowance]
        sections.append(header + excerpt)
        remaining -= len(header) + len(excerpt)
    return "".join(sections).strip()


class PdfReferenceLibrary:
    """Extract PDF text locally and retain only bounded in-memory context."""

    def load(self, paths: Iterable[str | Path]) -> ReferenceLoadResult:
        from pypdf import PdfReader

        unique_paths = tuple(dict.fromkeys(str(Path(path).resolve()) for path in paths))
        if len(unique_paths) > MAX_PDF_FILES:
            raise ValueError(f"Select at most {MAX_PDF_FILES} PDF files")

        documents: list[tuple[str, str]] = []
        accepted: list[str] = []
        warnings: list[str] = []
        page_count = 0

        for raw_path in unique_paths:
            path = Path(raw_path)
            if path.suffix.lower() != ".pdf":
                raise ValueError(f"Not a PDF file: {path.name}")
            if not path.is_file():
                raise ValueError(f"PDF file not found: {path.name}")
            if path.stat().st_size > MAX_PDF_BYTES:
                raise ValueError(f"PDF exceeds the 25 MB limit: {path.name}")

            reader = PdfReader(path)
            if reader.is_encrypted:
                raise ValueError(f"Password-protected PDFs are not supported: {path.name}")
            if len(reader.pages) > MAX_PAGES_PER_FILE:
                raise ValueError(f"PDF exceeds the 500-page limit: {path.name}")

            extracted_pages: list[str] = []
            for page in reader.pages:
                try:
                    extracted_pages.append(page.extract_text() or "")
                except Exception:
                    extracted_pages.append("")
            text = "\n".join(extracted_pages).strip()
            if not text:
                warnings.append(f"{path.name}: no extractable text (it may be scanned)")
                continue
            documents.append((path.name, text))
            accepted.append(str(path))
            page_count += len(reader.pages)

        context = build_reference_context(documents)
        if unique_paths and not context:
            raise ValueError("No readable text was found in the selected PDFs")
        if sum(len(text) for _, text in documents) > len(context):
            warnings.append("Reference text was truncated to the 80,000-character safety limit")
        return ReferenceLoadResult(
            context=context,
            paths=tuple(accepted),
            document_count=len(accepted),
            page_count=page_count,
            character_count=len(context),
            warnings=tuple(warnings),
        )
