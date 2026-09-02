import io
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.service import AIService
from app.core.config import settings
from app.core.exceptions import (
    AIProviderErrorException,
    AIProviderNotConfiguredException,
    AISummarizationFailedException,
    AITextTooLargeException,
)
from app.models.document import Document
from tests.test_pdf_extraction import generate_pdf_bytes


# ============================================================================
# Unit Tests: AI Providers & AIService
# ============================================================================

@pytest.mark.anyio
async def test_mock_ai_provider_deterministic_output() -> None:
    """Verify MockAIProvider generates deterministic summary without network calls."""
    provider = MockAIProvider()
    assert provider.provider_name == "mock"

    input_text = "Acme Corp quarterly report indicates 25% growth in SaaS revenue."
    summary_1 = await provider.generate_summary(input_text)
    summary_2 = await provider.generate_summary(input_text)

    assert isinstance(summary_1, str)
    assert summary_1 == summary_2
    assert "Acme Corp quarterly report" in summary_1
    assert "Summary (Mock):" in summary_1


@pytest.mark.anyio
async def test_ai_service_empty_and_whitespace_rejection() -> None:
    """Verify AIService rejects empty or whitespace-only input."""
    service = AIService(provider=MockAIProvider())

    with pytest.raises(AISummarizationFailedException, match="Cannot summarize empty"):
        await service.summarize_text("")

    with pytest.raises(AISummarizationFailedException, match="Cannot summarize empty"):
        await service.summarize_text("   \n\t  ")

    with pytest.raises(AISummarizationFailedException, match="Cannot summarize empty"):
        await service.summarize_text(None)


@pytest.mark.anyio
async def test_ai_service_max_chars_limit_enforced() -> None:
    """Verify AIService raises AITextTooLargeException when input exceeds limit."""
    service = AIService(provider=MockAIProvider())
    orig_limit = settings.AI_MAX_INPUT_CHARS
    settings.AI_MAX_INPUT_CHARS = 50

    try:
        oversized_text = "This is a long sentence that definitely exceeds fifty characters limit."
        with pytest.raises(AITextTooLargeException) as exc_info:
            await service.summarize_text(oversized_text)
        assert exc_info.value.error_code == "AI_TEXT_TOO_LARGE"
    finally:
        settings.AI_MAX_INPUT_CHARS = orig_limit


@pytest.mark.anyio
async def test_ai_service_unsupported_provider_resolution() -> None:
    """Verify AIService raises error on invalid provider configuration."""
    orig_provider = settings.AI_PROVIDER
    settings.AI_PROVIDER = "unsupported_llm"
    try:
        with pytest.raises(AIProviderNotConfiguredException):
            AIService._resolve_provider()
    finally:
        settings.AI_PROVIDER = orig_provider


@pytest.mark.anyio
async def test_openai_provider_missing_key_raises_configuration_error() -> None:
    """Verify OpenAIProvider raises AIProviderNotConfiguredException when key is missing."""
    orig_key = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = None
    try:
        provider = OpenAIProvider(api_key=None)
        with pytest.raises(AIProviderNotConfiguredException, match="OpenAI API key is missing"):
            await provider.generate_summary("Some document text")
    finally:
        settings.OPENAI_API_KEY = orig_key


@pytest.mark.anyio
async def test_openai_provider_mocked_success() -> None:
    """Verify OpenAIProvider correctly handles API response using mocked AsyncOpenAI client."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Mocked OpenAI generated summary."))
    ]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    provider = OpenAIProvider(api_key="test-key", client=mock_client)
    result = await provider.generate_summary("Document text to summarize")

    assert result == "Mocked OpenAI generated summary."
    mock_client.chat.completions.create.assert_awaited_once()


# ============================================================================
# Integration Tests: Document Summarization Endpoints & Database Persistence
# ============================================================================

def test_document_summarization_flow(client: TestClient, db_session: Session) -> None:
    """Verify the end-to-end document summarization flow with mock provider."""
    pdf_text = "Agreement terms: Licensor grants Licensee a non-exclusive license for 2026."
    pdf_bytes = generate_pdf_bytes([pdf_text])

    # 1. Upload
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("license.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # 2. Extract
    extract_res = client.post(f"/api/documents/{doc_id}/extract")
    assert extract_res.status_code == 200
    assert extract_res.json()["status"] == "processed"
    assert extract_res.json()["summary"] is None

    # 3. Summarize
    summarize_res = client.post(f"/api/documents/{doc_id}/summarize")
    assert summarize_res.status_code == 200
    data = summarize_res.json()

    assert data["id"] == doc_id
    assert data["status"] == "processed"
    assert data["summary"] is not None
    assert "Summary (Mock):" in data["summary"]

    # 4. Verify SQLite persistence
    db_doc = db_session.get(Document, doc_id)
    assert db_doc is not None
    assert db_doc.summary == data["summary"]
    assert db_doc.status == "processed"

    # 5. Verify GET /api/documents/{id} returns summary
    get_res = client.get(f"/api/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["summary"] == data["summary"]


def test_summarize_unextracted_document_rejected(client: TestClient) -> None:
    """Verify summarizing a document before text extraction returns 400 DOCUMENT_NOT_READY."""
    pdf_bytes = generate_pdf_bytes(["Unextracted text"])
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("unextracted.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]

    # Call summarize directly without extract
    response = client.post(f"/api/documents/{doc_id}/summarize")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_READY"


def test_summarize_empty_scanned_document_rejected(client: TestClient) -> None:
    """Verify summarizing an image-only / empty PDF (extracted_text is null) returns 400."""
    pdf_bytes = generate_pdf_bytes([""])
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("blank.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]
    client.post(f"/api/documents/{doc_id}/extract")

    response = client.post(f"/api/documents/{doc_id}/summarize")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_READY"


def test_summarize_non_existent_document_returns_404(client: TestClient) -> None:
    """Verify summarizing unknown document ID returns 404 DOCUMENT_NOT_FOUND."""
    response = client.post("/api/documents/unknown-doc-999/summarize")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_re_summarization_updates_summary(client: TestClient) -> None:
    """Verify re-summarizing an existing document updates and returns the summary cleanly."""
    pdf_text = "Master Services Agreement between Alpha and Beta."
    pdf_bytes = generate_pdf_bytes([pdf_text])

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("msa.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]
    client.post(f"/api/documents/{doc_id}/extract")

    # First summarization
    res_1 = client.post(f"/api/documents/{doc_id}/summarize")
    assert res_1.status_code == 200
    summary_1 = res_1.json()["summary"]

    # Second summarization
    res_2 = client.post(f"/api/documents/{doc_id}/summarize")
    assert res_2.status_code == 200
    summary_2 = res_2.json()["summary"]

    assert summary_1 == summary_2


def test_summarize_document_exceeding_max_chars_returns_413(client: TestClient) -> None:
    """Verify summarizing document text exceeding AI_MAX_INPUT_CHARS returns 413 error."""
    pdf_text = "This is a document whose text will exceed the temporary limit."
    pdf_bytes = generate_pdf_bytes([pdf_text])

    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("limit_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    doc_id = upload_res.json()["id"]
    client.post(f"/api/documents/{doc_id}/extract")

    orig_limit = settings.AI_MAX_INPUT_CHARS
    settings.AI_MAX_INPUT_CHARS = 10
    try:
        response = client.post(f"/api/documents/{doc_id}/summarize")
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "AI_TEXT_TOO_LARGE"
    finally:
        settings.AI_MAX_INPUT_CHARS = orig_limit
