import io
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document

SAMPLE_VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def test_valid_pdf_upload(client: TestClient) -> None:
    """Test successful PDF upload creates a record and returns 201."""
    files = {
        "file": ("sample_agreement.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")
    }
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["original_filename"] == "sample_agreement.pdf"
    assert data["stored_filename"].endswith(".pdf")
    assert data["stored_filename"] != "sample_agreement.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] == len(SAMPLE_VALID_PDF_BYTES)
    assert data["status"] == "uploaded"
    assert "created_at" in data
    assert "updated_at" in data


def test_uploaded_pdf_is_stored_on_disk(client: TestClient, test_storage: str) -> None:
    """Verify the uploaded PDF file actually exists on the filesystem with correct content."""
    files = {
        "file": ("invoice_2026.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")
    }
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    data = response.json()

    stored_file_path = Path(test_storage) / data["stored_filename"]
    assert stored_file_path.exists()
    assert stored_file_path.read_bytes() == SAMPLE_VALID_PDF_BYTES


def test_database_record_creation(client: TestClient, db_session: Session) -> None:
    """Verify SQLite database record matches uploaded metadata."""
    files = {
        "file": ("contract_v1.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")
    }
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    doc_id = response.json()["id"]

    db_doc = db_session.get(Document, doc_id)
    assert db_doc is not None
    assert db_doc.original_filename == "contract_v1.pdf"
    assert db_doc.file_path == f"storage/documents/{db_doc.stored_filename}"
    assert db_doc.status == "uploaded"
    assert db_doc.file_size == len(SAMPLE_VALID_PDF_BYTES)
    assert db_doc.extracted_text is None
    assert db_doc.summary is None


def test_database_stores_relative_portable_file_path(client: TestClient, db_session: Session) -> None:
    """Verify the database stores a relative, portable path instead of an absolute machine path."""
    files = {
        "file": ("portable_doc.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")
    }
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 201
    doc_id = response.json()["id"]

    db_doc = db_session.get(Document, doc_id)
    assert db_doc is not None

    # Must be a relative path and must not contain machine-specific drive letters or root prefixes
    assert not Path(db_doc.file_path).is_absolute()
    assert not db_doc.file_path.startswith(("\\", "/", "C:", "D:"))
    assert db_doc.file_path.startswith("storage/documents/")
    assert db_doc.file_path == f"storage/documents/{db_doc.stored_filename}"



def test_non_pdf_extension_rejected(client: TestClient) -> None:
    """Verify files with non-pdf extensions are rejected with 400 Bad Request."""
    files = {
        "file": ("document.txt", io.BytesIO(b"Hello world"), "text/plain")
    }
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_FILE_TYPE"


def test_fake_pdf_signature_rejected(client: TestClient) -> None:
    """Verify files named .pdf but without %PDF- magic bytes are rejected."""
    fake_pdf_bytes = b"This is plainly not a real PDF file despite the extension."
    files = {
        "file": ("fake_document.pdf", io.BytesIO(fake_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_PDF"


def test_file_larger_than_limit_rejected(client: TestClient) -> None:
    """Verify files larger than MAX_UPLOAD_SIZE_MB are rejected with 413 Payload Too Large."""
    orig_limit = settings.MAX_UPLOAD_SIZE_MB
    settings.MAX_UPLOAD_SIZE_MB = 1  # 1 MB for testing
    try:
        # Create 1.1 MB payload with valid PDF header
        oversized_bytes = b"%PDF-" + b"0" * (1024 * 1024 + 100)
        files = {
            "file": ("large_file.pdf", io.BytesIO(oversized_bytes), "application/pdf")
        }
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 413
        data = response.json()
        assert data["error"]["code"] == "FILE_TOO_LARGE"
    finally:
        settings.MAX_UPLOAD_SIZE_MB = orig_limit


def test_path_traversal_and_unsafe_filenames_stored_safely(client: TestClient, test_storage: str) -> None:
    """Verify directory traversal attempts in filename do not affect storage path."""
    dangerous_names = [
        "../../secret.pdf",
        r"..\..\..\system.pdf",
        "<script>alert('xss')</script>.pdf",
        "My Rental Agreement (Final) #2.pdf",
    ]

    for name in dangerous_names:
        files = {
            "file": (name, io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")
        }
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 201
        data = response.json()

        # The file on disk must be inside test_storage directory only
        stored_file_path = Path(test_storage) / data["stored_filename"]
        assert stored_file_path.exists()
        assert stored_file_path.parent.resolve() == Path(test_storage).resolve()


def test_list_documents(client: TestClient) -> None:
    """Verify listing documents returns paginated results in descending order of creation."""
    # Upload 2 documents
    client.post("/api/documents/upload", files={"file": ("doc1.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")})
    client.post("/api/documents/upload", files={"file": ("doc2.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")})

    response = client.get("/api/documents?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["original_filename"] == "doc2.pdf"
    assert data["items"][1]["original_filename"] == "doc1.pdf"


def test_get_document_by_id(client: TestClient) -> None:
    """Verify retrieving document metadata by ID."""
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("spec.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    response = client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["original_filename"] == "spec.pdf"


def test_get_unknown_document_returns_404(client: TestClient) -> None:
    """Verify querying non-existent document ID returns 404."""
    response = client.get("/api/documents/non-existent-uuid-1234")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_delete_document(client: TestClient, test_storage: str) -> None:
    """Verify deleting a document deletes both SQLite record and storage file."""
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("delete_me.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")},
    )
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    stored_path = Path(test_storage) / doc_data["stored_filename"]
    assert stored_path.exists()

    # Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == doc_id

    # Verify physical file is gone
    assert not stored_path.exists()

    # Verify database query now returns 404
    get_res = client.get(f"/api/documents/{doc_id}")
    assert get_res.status_code == 404


def test_delete_unknown_document_returns_404(client: TestClient) -> None:
    """Verify deleting non-existent document returns 404."""
    response = client.delete("/api/documents/unknown-id-5678")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_upload_database_failure_cleans_up_stored_file(client: TestClient, test_storage: str) -> None:
    """Verify that if database insertion fails after file is written, the file is cleaned up."""
    files = {
        "file": ("fail_test.pdf", io.BytesIO(SAMPLE_VALID_PDF_BYTES), "application/pdf")
    }

    with patch("app.repositories.document_repository.DocumentRepository.create", side_effect=RuntimeError("Simulated DB Crash")):
        response = client.post("/api/documents/upload", files=files)
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "UPLOAD_FAILED"

    # Verify no leaked files remain in test storage directory
    leftover_files = [f for f in Path(test_storage).glob("*.pdf")]
    assert len(leftover_files) == 0
