import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.references import (
    MAX_REFERENCE_CHARS,
    PdfReferenceLibrary,
    build_reference_context,
)


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    is_encrypted = False

    def __init__(self, _path):
        self.pages = [FakePage("Primary source fact one."), FakePage("Fact two.")]


class TestPdfReferences(unittest.TestCase):
    def test_context_has_document_boundaries_and_is_bounded(self):
        context = build_reference_context([("guide.pdf", "x" * (MAX_REFERENCE_CHARS * 2))])
        self.assertIn("REFERENCE: guide.pdf", context)
        self.assertLessEqual(len(context), MAX_REFERENCE_CHARS)

    def test_pdf_library_extracts_text_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "guide.pdf"
            pdf.write_bytes(b"%PDF-test")
            with patch("pypdf.PdfReader", FakeReader):
                result = PdfReferenceLibrary().load([pdf])

        self.assertEqual(result.document_count, 1)
        self.assertEqual(result.page_count, 2)
        self.assertIn("Primary source fact one", result.context)

    def test_rejects_non_pdf_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            text_file = Path(tmpdir) / "notes.txt"
            text_file.write_text("notes", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Not a PDF"):
                PdfReferenceLibrary().load([text_file])


if __name__ == "__main__":
    unittest.main()
