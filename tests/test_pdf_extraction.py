import io
from pathlib import Path
import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.document import Document


def generate_pdf_bytes(pages_text: list[str]) -> bytes:
    """Generate a valid in-memory PDF with the provided list of page texts using PyMuPDF."""
    doc = pymupdf.open()
    rect = pymupdf.Rect(50, 50, 550, 750)

    # Check for system font for extended unicode support if available
    font_file = None
    for candidate in [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if Path(candidate).exists():
            font_file = candidate
            break

    for text in pages_text:
        page = doc.new_page()
        if text:
            if font_file:
                page.insert_font(fontname="F0", fontfile=font_file)
                page.insert_textbox(rect, text, fontname="F0", fontsize=11)
            else:
                page.insert_textbox(rect, text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_single_page_pdf_extraction(client: TestClient, db_session: Session) -> None:
    """Verify single-page PDF text extraction via POST /api/documents/{id}/extract."""
    sample_text = "DocuMind AI: Intelligent document processing platform."
    pdf_bytes = generate_pdf_bytes([sample_text])

    # 1. Upload
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("single_page.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]
    assert upload_res.json()["status"] == "uploaded"
    assert upload_res.json()["extracted_text"] is None

    # 2. Extract
    extract_res = client.post(f"/api/documents/{doc_id}/extract")
    assert extract_res.status_code == 200
    data = extract_res.json()

    assert data["id"] == doc_id
    assert data["status"] == "processed"
    assert data["extracted_text"] is not None
    assert sample_text in data["extracted_text"]

    # 3. Verify SQLite persistence
    db_doc = db_session.get(Document, doc_id)
    assert db_doc is not None
    assert db_doc.status == "processed"
    assert db_doc.extracted_text is not None
    assert sample_text in db_doc.extracted_text


def test_multipage_pdf_extraction_and_page_order(client: TestClient) -> None:
    """Verify multi-page PDF text extraction preserves strict page ordering."""
    page_1 = "Chapter 1: Introduction to Machine Learning"
    page_2 = "Chapter 2: Retrieval Augmented Generation Foundations"
    page_3 = "Chapter 3: Production Deployment and Scalability"

    pdf_bytes = generate_pdf_bytes([page_1, page_2, page_3])

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("multipage.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    extract_res = client.post(f"/api/documents/{doc_id}/extract")
    assert extract_res.status_code == 200
    extracted_text = extract_res.json()["extracted_text"]

    # Verify all pages are present
    assert page_1 in extracted_text
    assert page_2 in extracted_text
    assert page_3 in extracted_text

    # Verify page order: Page 1 < Page 2 < Page 3
    idx_1 = extracted_text.index(page_1)
    idx_2 = extracted_text.index(page_2)
    idx_3 = extracted_text.index(page_3)
    assert idx_1 < idx_2 < idx_3


def test_unicode_text_extraction(client: TestClient) -> None:
    """Verify unicode characters (currencies, accents, and symbols) are extracted accurately."""
    unicode_content = (
        "Global Trade Agreement 2026\n"
        "English: Total revenue is €50,000 and ₹4,000,000.\n"
        "Accents: Résumé, Über, Peña, São Paulo.\n"
        "Symbols: Alpha & Beta test #1 (100%)."
    )
    pdf_bytes = generate_pdf_bytes([unicode_content])

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("unicode_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    extract_res = client.post(f"/api/documents/{doc_id}/extract")
    assert extract_res.status_code == 200
    extracted_text = extract_res.json()["extracted_text"]

    assert "Global Trade Agreement 2026" in extracted_text
    assert "€50,000" in extracted_text
    assert "₹4,000,000" in extracted_text
    assert "Résumé" in extracted_text
    assert "São Paulo" in extracted_text



def test_empty_or_image_only_pdf(client: TestClient, db_session: Session) -> None:
    """Verify PDFs with no extractable text process cleanly without false OCR claims."""
    # Blank PDF page
    pdf_bytes = generate_pdf_bytes([""])

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("blank.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    extract_res = client.post(f"/api/documents/{doc_id}/extract")
    assert extract_res.status_code == 200
    data = extract_res.json()
    assert data["status"] == "processed"
    assert data["extracted_text"] is None

    # Verify in DB
    db_doc = db_session.get(Document, doc_id)
    assert db_doc is not None
    assert db_doc.status == "processed"
    assert db_doc.extracted_text is None


def test_corrupted_pdf_extraction_fails_gracefully(client: TestClient, db_session: Session) -> None:
    """Verify corrupted PDF triggers 400 DOCUMENT_EXTRACTION_FAILED and marks document status='failed'."""
    # Magic bytes pass upload validation, but the remainder is corrupted garbage
    corrupted_pdf_bytes = b"%PDF-1.4\nCorrupted binary garbage stream <<>> non-readable %EOF"

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("corrupted.pdf", io.BytesIO(corrupted_pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    extract_res = client.post(f"/api/documents/{doc_id}/extract")
    assert extract_res.status_code == 400
    err_data = extract_res.json()
    assert err_data["error"]["code"] == "DOCUMENT_EXTRACTION_FAILED"

    # Verify status in database transitioned to 'failed'
    db_doc = db_session.get(Document, doc_id)
    assert db_doc is not None
    assert db_doc.status == "failed"


def test_extract_unknown_document_returns_404(client: TestClient) -> None:
    """Verify extracting non-existent document ID returns 404."""
    response = client.post("/api/documents/non-existent-uuid-1234/extract")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_repeated_extraction_is_deterministic(client: TestClient) -> None:
    """Verify calling extract multiple times safely re-extracts text without corruption."""
    sample_text = "Deterministic repeated extraction test."
    pdf_bytes = generate_pdf_bytes([sample_text])

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("repeat.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    # First extraction
    res_1 = client.post(f"/api/documents/{doc_id}/extract")
    assert res_1.status_code == 200
    text_1 = res_1.json()["extracted_text"]

    # Second extraction
    res_2 = client.post(f"/api/documents/{doc_id}/extract")
    assert res_2.status_code == 200
    text_2 = res_2.json()["extracted_text"]

    assert text_1 == text_2
    assert sample_text in text_2


def test_get_document_returns_extracted_text_after_extraction(client: TestClient) -> None:
    """Verify GET /api/documents/{id} returns the extracted text after extraction is triggered."""
    sample_text = "Executive Summary: Q4 Financial Report."
    pdf_bytes = generate_pdf_bytes([sample_text])

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("q4_report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    # Before extraction: extracted_text is None
    get_before = client.get(f"/api/documents/{doc_id}")
    assert get_before.status_code == 200
    assert get_before.json()["extracted_text"] is None
    assert get_before.json()["status"] == "uploaded"

    # Perform extraction
    client.post(f"/api/documents/{doc_id}/extract")

    # After extraction: extracted_text is populated
    get_after = client.get(f"/api/documents/{doc_id}")
    assert get_after.status_code == 200
    assert get_after.json()["extracted_text"] is not None
    assert sample_text in get_after.json()["extracted_text"]
    assert get_after.json()["status"] == "processed"
