# DocuMind AI

> *Turn documents into answers.*

DocuMind AI is an intelligent document processing and question-answering platform designed to extract information and deliver precise answers from complex documents.

---

## 📌 Project Status

**Current Phase:** Phase 4 — AI Provider Abstraction + Document Summarization

The platform features a modular AI provider abstraction supporting offline deterministic mocking and live OpenAI integration, coupled with document text extraction and persistent summarization.

### ✅ Implemented Features:
- **PDF Upload & Validation:** Enforces `.pdf` extension, MIME validation, file size limits (`MAX_UPLOAD_SIZE_MB`), and `%PDF-` binary signature check.
- **Safe & Collision-Resistant Storage:** Portable relative storage paths (`storage/documents/<uuid>.pdf`) with physical resolution from configured `STORAGE_DIR`.
- **SQLite Document Persistence:** Database records for document metadata, extracted text, and generated summaries using SQLAlchemy 2.x.
- **Page-by-Page PDF Text Extraction:** Dedicated `PDFExtractionService` powered by PyMuPDF extracting text strictly in document page order with Unicode normalization.
- **Provider-Independent AI Architecture:**
  - `AIProvider` base interface decoupling application code from specific AI vendors.
  - `MockAIProvider` for deterministic, offline testing without API keys or network latency.
  - `OpenAIProvider` using `AsyncOpenAI` with structured anti-injection system prompts and robust error translation.
  - `AIService` orchestrator enforcing text boundary limits (`AI_MAX_INPUT_CHARS`) and input validation.
- **Document Summarization Endpoint:** `POST /api/documents/{id}/summarize` triggers AI summarization and persists the result in `Document.summary`.
- **Status Lifecycle Management:** Tracks document state through `uploaded` ➔ `processing` ➔ `processed` (or `failed` on corrupted files).
- **Service Health Monitoring:** `GET /health` service endpoint.
- **Automated Test Suite:** 35 pytest test cases covering foundation, upload security, extraction behaviors, AI abstraction, and summarization workflows.

### ⏳ Planned (Future Milestones):
- **OCR Engine:** Tesseract OCR for scanned / image-only documents.
- **RAG & Interactive Q&A:** Vector embeddings, chunking, semantic retrieval, and conversational document question-answering.
- **Frontend:** Modern Web UI (HTML/CSS/JavaScript).

> [!NOTE]
> **Important:** Interactive Chat/Q&A, Vector Databases/Embeddings, and OCR are not implemented in Phase 4 and are planned for subsequent milestones.

---

## 🛠️ Technology Stack

- **Language:** Python 3.12+ (tested with Python 3.13)
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **PDF Engine:** [PyMuPDF](https://pymupdf.readthedocs.io/)
- **AI / LLM Integration:** [OpenAI Python SDK](https://github.com/openai/openai-python)
- **ORM / Database:** [SQLAlchemy 2.x](https://www.sqlalchemy.org/) with SQLite
- **Validation & Settings:** [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Testing:** [pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)

---

## 📁 Project Structure

```
documind-ai/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & exception handlers
│   │
│   ├── ai/                      # Provider-independent AI layer
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract AIProvider interface
│   │   ├── service.py           # AIService orchestration & boundary enforcement
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── mock.py          # Deterministic offline MockAIProvider
│   │       └── openai_provider.py # OpenAI AsyncOpenAI provider
│   │
│   ├── api/                     # API routing and endpoint handlers
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py      # Router aggregator
│   │       ├── health.py        # Health check endpoint (/health)
│   │       └── documents.py     # Document, extraction & summarization endpoints
│   │
│   ├── core/                    # Core configuration and infrastructure
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic Settings & environment config
│   │   ├── database.py          # SQLAlchemy engine, session & init_db
│   │   ├── exceptions.py        # Centralized application exception classes
│   │   └── logging.py           # Standard centralized logging
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── document.py          # Document database model
│   │
│   ├── schemas/                 # Pydantic validation schemas
│   │   ├── __init__.py
│   │   └── document.py          # Document response schemas
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── document_service.py  # Document storage, lifecycle & summarization orchestration
│   │   └── pdf_extraction_service.py # PyMuPDF text extraction engine
│   │
│   └── repositories/            # Data access layer
│       ├── __init__.py
│       └── document_repository.py # Document CRUD operations
│
├── tests/                       # Automated test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures for isolated db & storage
│   ├── test_health.py           # Health check endpoint tests
│   ├── test_documents.py        # Document upload, validation & management tests
│   ├── test_pdf_extraction.py   # PDF text extraction & edge cases tests
│   └── test_ai_summarization.py # AI provider & summarization tests
│
├── storage/                     # Storage for document files
│   ├── .gitkeep
│   └── documents/               # Stored uploaded PDF files
│       └── .gitkeep
│
├── data/                        # Local SQLite database directory (.gitkeep)
│   └── .gitkeep
│
├── docs/                        # Project documentation (.gitkeep)
│   └── .gitkeep
│
├── .env.example                 # Example environment variables template
├── .gitignore                   # Git ignore patterns
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
└── LICENSE                      # MIT License
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health status | `200 OK` |
| `POST` | `/api/documents/upload` | Upload & validate a PDF file | `201 Created` |
| `GET` | `/api/documents` | List uploaded documents with pagination (`?skip=0&limit=20`) | `200 OK` |
| `GET` | `/api/documents/{document_id}` | Retrieve document metadata, text & summary | `200 OK` |
| `POST` | `/api/documents/{document_id}/extract` | Trigger PDF text extraction via PyMuPDF | `200 OK` |
| `POST` | `/api/documents/{document_id}/summarize` | Generate & store AI summary of extracted text | `200 OK` |
| `DELETE` | `/api/documents/{document_id}` | Delete document record and stored file | `200 OK` |
| `GET` | `/docs` | Interactive Swagger API documentation | `200 OK` |

---

## 🤖 AI Configuration

The application supports multiple AI providers configurable via environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `mock` | Selected provider: `mock` (offline, zero-config) or `openai` |
| `OPENAI_API_KEY` | *(None)* | OpenAI API Secret Key (required only when `AI_PROVIDER=openai`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model identifier |
| `AI_MAX_INPUT_CHARS` | `100000` | Maximum character limit for text sent to the AI provider |

### Running with Mock AI (Default)
In `mock` mode (default for development and automated testing), no API key or internet access is needed. The application returns realistic, deterministic summaries.

### Running with OpenAI
To enable OpenAI summarization in production:
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12 or newer installed on your system.
- Git installed.

### 2. Set Up Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the `.env.example` template:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

### 5. Run the Application

Start the local development server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Interactive API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 6. Run Automated Tests

Execute the full test suite using `pytest`:

```bash
pytest -v
```

---

## 🔒 Security Note

- **Untrusted Input Protection:** Document text is treated strictly as data within bounded XML tags in system prompts to prevent prompt injection overrides.
- **Zero Privacy Leakage in Logs:** Document text, full prompts, generated summaries, and API keys are strictly excluded from application logs.
- **Zero Secrets in Git:** Sensitive credentials and local databases (`*.db`, `*.sqlite`) are ignored by `.gitignore`.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
