"""
Parses raw file bytes into a list of `ParsedPage` units, each carrying the
page number and any detected section heading. This is the single place
where format-specific logic lives, so chunking_service.py never has to
know whether content came from a PDF or a URL.
"""

import io
import re
from dataclasses import dataclass

import httpx
import markdown as md_lib
from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.exceptions import AppException, ExternalServiceException
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedPage:
    page_number: int | None
    section: str | None
    text: str


class ParsingService:
    def parse(self, source_type: str, content: bytes | None = None, url: str | None = None) -> list[ParsedPage]:
        if source_type == "pdf":
            return self._parse_pdf(content)
        if source_type == "docx":
            return self._parse_docx(content)
        if source_type == "txt":
            return self._parse_txt(content)
        if source_type == "markdown":
            return self._parse_markdown(content)
        if source_type == "url":
            return self._parse_url(url)
        raise AppException(f"Unsupported source type for parsing: {source_type}")

    def _parse_pdf(self, content: bytes) -> list[ParsedPage]:
        try:
            reader = PdfReader(io.BytesIO(content))
        except Exception as exc:
            raise AppException("Could not read this PDF — it may be corrupted.") from exc

        pages: list[ParsedPage] = []
        ocr_needed_pages = 0

        for i, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                ocr_needed_pages += 1
                text = self._ocr_pdf_page(page)
            if text:
                pages.append(ParsedPage(page_number=i, section=None, text=text))

        if ocr_needed_pages:
            logger.info("OCR fallback used for %d page(s) with no extractable text.", ocr_needed_pages)

        if not pages:
            raise AppException("No extractable text found in this PDF, even after OCR.")
        return pages

    def _ocr_pdf_page(self, page) -> str:
        """
        OCR fallback for scanned/image-only PDF pages using pytesseract.
        Requires the `tesseract-ocr` system binary to be installed in the
        runtime image (added to Dockerfile).
        """
        try:
            import pytesseract
            from pdf2image import convert_from_bytes

            writer_bytes = io.BytesIO()
            from pypdf import PdfWriter

            writer = PdfWriter()
            writer.add_page(page)
            writer.write(writer_bytes)
            writer_bytes.seek(0)

            images = convert_from_bytes(writer_bytes.read(), dpi=200)
            text_parts = [pytesseract.image_to_string(img) for img in images]
            return "\n".join(text_parts).strip()
        except Exception as exc:
            logger.warning("OCR fallback failed for a page: %s", exc)
            return ""

    def _parse_docx(self, content: bytes) -> list[ParsedPage]:
        try:
            doc = DocxDocument(io.BytesIO(content))
        except Exception as exc:
            raise AppException("Could not read this DOCX file — it may be corrupted.") from exc

        pages: list[ParsedPage] = []
        current_section: str | None = None
        buffer: list[str] = []

        def flush():
            if buffer:
                pages.append(ParsedPage(page_number=None, section=current_section, text="\n".join(buffer)))
                buffer.clear()

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style and para.style.name and para.style.name.lower().startswith("heading"):
                flush()
                current_section = text
                continue
            buffer.append(text)
        flush()

        if not pages:
            raise AppException("No extractable text found in this DOCX file.")
        return pages

    def _parse_txt(self, content: bytes) -> list[ParsedPage]:
        text = content.decode("utf-8", errors="ignore").strip()
        if not text:
            raise AppException("This text file appears to be empty.")
        return [ParsedPage(page_number=None, section=None, text=text)]

    def _parse_markdown(self, content: bytes) -> list[ParsedPage]:
        raw = content.decode("utf-8", errors="ignore")
        if not raw.strip():
            raise AppException("This markdown file appears to be empty.")

        sections: list[ParsedPage] = []
        current_heading: str | None = None
        buffer: list[str] = []

        def flush():
            if buffer:
                sections.append(ParsedPage(page_number=None, section=current_heading, text="\n".join(buffer)))
                buffer.clear()

        for line in raw.splitlines():
            heading_match = re.match(r"^#{1,6}\s+(.*)", line)
            if heading_match:
                flush()
                current_heading = heading_match.group(1).strip()
                continue
            if line.strip():
                buffer.append(line)
        flush()

        return sections or [ParsedPage(page_number=None, section=None, text=raw)]

    def _parse_url(self, url: str) -> list[ParsedPage]:
        try:
            response = httpx.get(url, timeout=20, follow_redirects=True, headers={"User-Agent": "ResearchAssistant/1.0"})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceException(f"Failed to fetch URL: {exc}") from exc

        html = response.text
        text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            raise AppException("No readable text content found at this URL.")
        return [ParsedPage(page_number=None, section=None, text=text)]


parsing_service = ParsingService()
