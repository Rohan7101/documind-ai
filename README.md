# DocuMind AI

> *Turn documents into answers.*

DocuMind AI is an intelligent document processing and question-answering platform designed to extract information and deliver precise answers from complex documents.

---

## 📌 Project Status

**Current Phase:** Phase 2 - Document Management Foundation

The document management foundation is implemented with secure file validation, local disk persistence, SQLite metadata storage, pagination, retrieval, and cascading deletion.

### ✅ Implemented Features:
- **PDF File Upload & Validation:** Validates `.pdf` extension, MIME types, file size limits (`MAX_UPLOAD_SIZE_MB`), and `%PDF-` binary magic byte signatures.
- **Safe & Collision-Resistant Storage:** Files are stored in `storage/documents/` using generated UUID filenames (`<uuid>.pdf`), completely isolating filesystem storage from unsafe client filenames.
- **SQLite Document Metadata:** Persists document metadata (`id`, `original_filename`, `stored_filename`, `file_size`, `mime_type`, `status`, timestamps) using SQLAlchemy 2.x.
- **Document Management Endpoints:** Full CRUD operations for uploading, paginating, inspecting, and deleting documents with transactional failure cleanup.
- **Service Health Monitoring:** `GET /health` service status endpoint.
- **Automated Testing:** Pytest suite with isolated test database and temporary storage fixtures.

### ⏳ Planned (Future Milestones):
- **Document Parsing & Text Extraction:** PyMuPDF integration.
- **OCR Engine:** Tesseract OCR for scanned documents/images.
- **AI / LLM Integration:** Embeddings, vector indexing, document summarization, and interactive Q&A.
- **Frontend:** Modern Web UI (HTML/CSS/JavaScript).

---

## 🛠️ Technology Stack

- **Language:** Python 3.12+ (tested with Python 3.13)
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
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
│   ├── api/                     # API routing and endpoint handlers
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py      # Router aggregator
│   │       ├── health.py        # Health check endpoint (/health)
│   │       └── documents.py     # Document management endpoints (/api/documents)
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
│   │   └── document_service.py  # Document upload, storage & lifecycle logic
│   │
│   └── repositories/            # Data access layer
│       ├── __init__.py
│       └── document_repository.py # Document CRUD operations
│
├── tests/                       # Automated test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures for isolated db & storage
│   ├── test_health.py           # Health check endpoint tests
│   └── test_documents.py        # Document upload, validation & management tests
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
| `GET` | `/api/documents/{document_id}` | Retrieve document metadata by ID | `200 OK` |
| `DELETE` | `/api/documents/{document_id}` | Delete document record and stored file | `200 OK` |
| `GET` | `/docs` | Interactive Swagger API documentation | `200 OK` |

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

Execute the test suite using `pytest`:

```bash
pytest -v
```

---

## 🔒 Security Note

- **Path Traversal Protection:** Uploaded files are stored with unique UUID filenames and never use client-provided filenames on the local filesystem.
- **Magic Bytes Validation:** Uploaded PDFs are validated for the `%PDF-` signature to prevent executable or script files masquerading as PDFs.
- **Zero Secrets in Git:** Sensitive credentials and local databases (`*.db`, `*.sqlite`) are ignored by `.gitignore`.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
