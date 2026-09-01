import re
from pathlib import Path
from typing import Optional
import pymupdf

from app.core.exceptions import DocumentExtractionException
from app.core.logging import logger


class PDFExtractionService:
    """Service dedicated to extracting, cleaning, and ordering text from PDF files using PyMuPDF."""

    @staticmethod
    def _clean_page_text(text: str) -> str:
        """Clean extracted page text while preserving line breaks, words, and unicode content."""
        if not text:
            return ""

        # Normalize non-breaking and zero-width spaces to standard spaces
        normalized = text.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")

        # Normalize line endings to LF
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

        # Strip trailing whitespace on each line
        lines = [line.rstrip() for line in normalized.split("\n")]
        cleaned = "\n".join(lines)

        # Collapse more than two consecutive newlines into two
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()


    def extract_text_from_file(self, file_path: Path | str) -> Optional[str]:
        """Open a PDF from disk, extract text page by page in document order, and return normalized text.

        Returns:
            The extracted text string, or None if the PDF contains no extractable text.

        Raises:
            DocumentExtractionException: If the PDF cannot be opened or is corrupted.
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            logger.error(f"PDF file not found on disk: {path_obj}")
            raise DocumentExtractionException("The document file could not be found on storage.")

        doc: Optional[pymupdf.Document] = None
        try:
            doc = pymupdf.open(str(path_obj))

            if doc.is_encrypted:
                logger.warning(f"Encrypted PDF detected: {path_obj}")
                raise DocumentExtractionException("Encrypted or password-protected PDFs are not supported.")

            page_texts: list[str] = []

            # Process pages strictly in document page order
            for page_num in range(len(doc)):
                page = doc[page_num]
                raw_text = page.get_text("text")
                cleaned_page = self._clean_page_text(raw_text)
                if cleaned_page:
                    page_texts.append(cleaned_page)

            if not page_texts:
                logger.info(f"No extractable text found in PDF: {path_obj} (may be image-only / scanned)")
                return None

            combined_text = "\n\n".join(page_texts).strip()
            return combined_text if combined_text else None

        except DocumentExtractionException:
            raise
        except Exception as err:
            logger.error(f"Error during PDF extraction on {path_obj}: {err}", exc_info=True)
            raise DocumentExtractionException("Unable to extract text from the document. The file may be damaged or invalid.")
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception as close_err:
                    logger.warning(f"Error closing PDF document {path_obj}: {close_err}")
