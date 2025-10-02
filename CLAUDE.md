# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Document Search & Retrieval System** for an internal sales department. The system enables sales agents to quickly find information in PDF documentation (maintenance manuals, operation instructions, spare parts catalogs) by reducing search time from 30 minutes to <3 minutes (90% improvement).

### Architecture
- **Backend**: FastAPI (Python 3.10+)
- **Search Engine**: Elasticsearch 8.11+ (BM25 full-text search)
- **PDF Parsing**: LandingAI ADE SDK (`dpt-2-latest` model)
- **Summarization**: Claude Haiku 3 (`claude-3-haiku-20240307`)
- **Database**: PostgreSQL (document metadata)
- **Deployment**: Self-hosted (MVP), scalable to production cluster

## Current Status

**Phase**: Planning Complete - Ready for Implementation
**Documents**:
- ✅ [Product Requirements Document (PRD)](tasks/prd-document-search-system.md) - v1.3
- ✅ [Technical Design Document (TDD)](docs/technical_design_document.md) - v1.1
- ✅ [Task List](tasks/tasks-prd-document-search-system.md) - 10 parent tasks, 83 sub-tasks
- ✅ [Context Session](docs/context_session.md) - Project tracking and decisions

**Next Step**: Begin Task 1.1 - Initialize Python project structure

## Setup

### Prerequisites
- Python 3.10+
- Elasticsearch 8.11+
- PostgreSQL 14+
- Git

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .myenv
source .myenv/bin/activate  # On Windows: .myenv\Scripts\activate

# Install dependencies (will be created in Task 1.2)
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the root directory with:
```bash
# API Keys
VISION_AGENT_API_KEY=your_landingai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Elasticsearch
ELASTICSEARCH_URL=https://localhost:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=your_es_password

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/docsearch

# Application
API_KEY=your_secure_api_key
PDF_STORAGE_PATH=/data/pdfs
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100
```

## Development Workflow

### Task Implementation Process
Follow the task list in [tasks/tasks-prd-document-search-system.md](tasks/tasks-prd-document-search-system.md):

1. **One sub-task at a time** - Complete each sub-task fully before proceeding
2. **Mark completed** - Update task list: `[ ]` → `[x]`
3. **Test after parent task** - Run `pytest` when all sub-tasks complete
4. **Commit after parent task** - Use conventional commit format
5. **Wait for approval** - Ask user before starting next sub-task

### Running the Application (after implementation)
```bash
# Start Elasticsearch
./scripts/start_elasticsearch.sh

# Initialize database
python scripts/init_db.py

# Run FastAPI application
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e          # End-to-end tests only
```

## Project Structure

```
doc-parser/
├── .env                    # Environment variables (git-ignored)
├── .gitignore
├── CLAUDE.md               # This file - project guidance
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
│
├── docs/                  # Documentation
│   ├── context_session.md
│   ├── technical_design_document.md
│   └── API.md
│
├── tasks/                 # Planning documents
│   ├── prd-document-search-system.md
│   └── tasks-prd-document-search-system.md
│
├── src/                   # Application code
│   ├── __init__.py
│   ├── main.py           # FastAPI entry point
│   ├── config.py         # Configuration management
│   │
│   ├── api/              # API routes
│   │   ├── documents.py
│   │   └── search.py
│   │
│   ├── models/           # Pydantic schemas
│   │   ├── document.py
│   │   └── search.py
│   │
│   ├── services/         # Business logic
│   │   ├── pdf_parser.py
│   │   ├── summarizer.py
│   │   ├── document_processor.py
│   │   └── search_service.py
│   │
│   ├── db/               # Database clients
│   │   ├── elasticsearch.py
│   │   └── postgres.py
│   │
│   └── utils/            # Utilities
│       ├── logging.py
│       └── auth.py
│
├── tests/                # Test files
│   ├── conftest.py
│   ├── test_pdf_parser.py
│   ├── test_summarizer.py
│   ├── test_document_processor.py
│   ├── test_search_service.py
│   ├── test_api_documents.py
│   ├── test_api_search.py
│   └── test_e2e_user_flow.py
│
└── scripts/              # Deployment scripts
    ├── start_elasticsearch.sh
    ├── init_db.py
    └── load_sample_data.py
```

## Key Technical Details

### Document Processing Pipeline
1. **Upload**: Accept PDF via `/api/v1/documents/upload`
2. **Parse**: Extract text/tables using LandingAI (`dpt-2-latest`)
3. **Chunk**: Split markdown into page-level chunks
4. **Summarize**: Generate summaries with Claude Haiku 3
5. **Index**: Store in Elasticsearch for search

### Search Implementation
- **Algorithm**: Elasticsearch BM25 (keyword-based full-text search)
- **Fuzzy Matching**: AUTO (1-2 character edits based on term length)
- **Field Boosting**: `part_numbers^3`, `machine_model^2.5`, `content^2`, `summary^1.5`
- **Highlighting**: Extract snippets with matched terms
- **Filters**: Category, machine model, date range
- **Performance Target**: <3s search latency (p95)

### Cost Structure
- **Elasticsearch**: $0/month (Basic tier free for self-managed)
- **LandingAI**: ~$0.01-0.05 per page (estimate)
- **Claude Haiku 3**: $0.0037 per document (summaries cached)
- **Infrastructure**: ~$75-300/month (server/VM)
- **Total MVP**: ~$75/month operational costs

## API Endpoints (Planned)

### Document Management
- `POST /api/v1/documents/upload` - Upload PDF document
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents` - List documents (paginated)
- `DELETE /api/v1/documents/{id}` - Delete document
- `GET /api/v1/documents/{id}/download` - Download PDF

### Search
- `POST /api/v1/search` - Search documents with filters

### Health
- `GET /health` - Health check endpoint

---

# important-instruction-reminders

## Task Execution Rules
- **Follow the task list strictly** - Work through tasks in order from [tasks-prd-document-search-system.md](tasks/tasks-prd-document-search-system.md)
- **One sub-task at a time** - Complete fully, mark `[x]`, then wait for user approval
- **Test before commit** - Run `pytest` after completing all sub-tasks under a parent task
- **Commit after parent task** - Use conventional commit format when parent task is complete
- **Update task list file** - Keep task list up-to-date as you work

## Code Quality Standards
- **Type hints** - Use Python type hints for all function signatures
- **Docstrings** - Add docstrings to all public functions/classes
- **Error handling** - Implement proper try-catch with logging
- **Testing** - Write tests for all new code (target >80% coverage)
- **Logging** - Use structured logging with appropriate levels
- **Security** - Validate all inputs, use parameterized queries, never commit secrets

## Important Constraints
- **Do what has been asked; nothing more, nothing less**
- **NEVER create files unless they're absolutely necessary** for achieving your goal
- **ALWAYS prefer editing an existing file** to creating a new one
- **NEVER proactively create documentation files** (*.md) or README files unless explicitly requested
- **Only commit when explicitly asked** or when completing a parent task per the protocol
- **Use existing validated code** from [playground.ipynb](playground.ipynb) as reference for LandingAI integration

## Reference Documents
- **PRD**: [tasks/prd-document-search-system.md](tasks/prd-document-search-system.md) - Requirements and user stories
- **TDD**: [docs/technical_design_document.md](docs/technical_design_document.md) - Architecture and design
- **Task List**: [tasks/tasks-prd-document-search-system.md](tasks/tasks-prd-document-search-system.md) - Implementation tasks
- **Context**: [docs/context_session.md](docs/context_session.md) - Project decisions and status
