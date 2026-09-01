# DocuMind AI

> *Turn documents into answers.*

DocuMind AI is an intelligent document processing and question-answering platform designed to extract information and deliver precise answers from complex documents.

---

## 📌 Project Status

**Current Phase:** Foundation / Development (Milestone 1)

The project foundation is initialized with core configuration, database connection scaffolding, logging, structured error handling, health monitoring, and test suites. Advanced document processing, OCR, AI integration, and user interfaces are planned for subsequent milestones.

---

## 🛠️ Planned Technology Stack

### Current Foundation:
- **Language:** Python 3.12+ (tested with Python 3.13)
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **ORM / Database:** [SQLAlchemy 2.x](https://www.sqlalchemy.org/) with SQLite
- **Validation & Settings:** [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Testing:** [pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)

### Planned (Future Milestones):
- **Document Ingestion & Parsing:** PyMuPDF
- **OCR Engine:** Tesseract OCR
- **Intelligence:** LLM API / Retrieval-Augmented Generation (RAG)
- **Frontend:** Modern Web UI (HTML/CSS/JavaScript)

---

## 📁 Project Structure

```
documind-ai/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint
│   │
│   ├── api/                     # API routing and endpoint handlers
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py        # Health check endpoint (/health)
│   │
│   ├── core/                    # Core configuration and infrastructure
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic Settings & environment config
│   │   ├── database.py          # SQLAlchemy engine & session dependency
│   │   └── logging.py           # Standard centralized logging
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   └── __init__.py
│   │
│   ├── schemas/                 # Pydantic validation schemas
│   │   └── __init__.py
│   │
│   ├── services/                # Business logic layer
│   │   └── __init__.py
│   │
│   └── repositories/            # Data access layer
│       └── __init__.py
│
├── tests/                       # Automated test suite
│   ├── __init__.py
│   └── test_health.py           # Health check endpoint tests
│
├── storage/                     # Storage for document files (.gitkeep)
│   └── .gitkeep
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

**Windows (cmd):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the `.env.example` template to create your local `.env` file:

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

- API Base URL: `http://127.0.0.1:8000`
- Interactive API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Alternative API Docs (ReDoc): `http://127.0.0.1:8000/redoc`
- Health Check: `http://127.0.0.1:8000/health`

### 6. Run Automated Tests

Execute the test suite using `pytest`:

```bash
pytest
```

---

## 🔒 Security Note

- **Never commit `.env` files or API secrets** to version control.
- All sensitive credentials and local database files (`*.db`, `*.sqlite`) are ignored by `.gitignore`.
- Only commit safe template configuration files like `.env.example`.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
