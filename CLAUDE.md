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

**Phase**: Phase 1A Complete - All Core MVP Features Implemented
**Completed Tasks**:
- ✅ Task 1.0 - Project Setup & Infrastructure
- ✅ Task 2.0 - PDF Processing & Summarization
- ✅ Task 3.0 - Elasticsearch Integration
- ✅ Task 4.0 - Search API Implementation
- ✅ Task 5.0 - Document Management API
- ✅ Task 6.0 - Testing & Quality Assurance (114 tests passing)
- ✅ Task 7.0 - Deployment & Documentation
- ✅ Search UI - Interactive HTML interface with full content display

**Documents**:
- ✅ [Product Requirements Document (PRD)](tasks/prd-document-search-system.md) - v1.3
- ✅ [Technical Design Document (TDD)](docs/technical_design_document.md) - v1.1
- ✅ [Task List](tasks/tasks-prd-document-search-system.md) - 10 parent tasks, 83 sub-tasks
- ✅ [Context Session](docs/context_session.md) - Project tracking and decisions

**Current State**:
- Backend API fully functional with 114/114 tests passing
- Document management endpoints complete (upload, list, get, delete, download)
- Elasticsearch indexing and search working
- HTML search UI available at root URL (`/`)
- Full content display with preserved table structures
- **User feedback system** with thumbs up/down rating (Issue #001 ✅)
- **Feedback-based search ranking** with score boosting
- **Professional pitch page** at `/pitch.html` with demo video and ROI calculations
- **URL-based personalization** system for customized business cases (see [docs/pitch-personalization-guide.md](docs/pitch-personalization-guide.md))
- API key authentication implemented
- Large PDF handling with automatic 50-page limiting
- Comprehensive deployment scripts and documentation

**Production Ready**: MVP complete with learning capabilities and sales enablement materials

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

### Issue Management

#### Creating New Issues
When creating a new issue, follow these guidelines:

1. **Numbering**: Issues are numbered sequentially starting from 001 (use 3 digits: 001, 002, ..., 099, 100)
2. **Filename Format**: `{number}-{status}-{short-title}.md`
   - Example: `001-open-user-scoring-learning.md`
   - Example: `042-in-progress-fix-pdf-parsing.md`
   - Example: `015-completed-add-fuzzy-search.md`

3. **Status Values**:
   - `open` - Issue identified, not yet started
   - `in-progress` - Currently being worked on
   - `completed` - Issue resolved and verified
   - `wontfix` - Issue acknowledged but will not be fixed

4. **Required Sections**:
   ```markdown
   # Issue #{number}: {Title}

   **Status**: {open|in-progress|completed|wontfix}
   **Priority**: {Low|Medium|High|Critical}
   **Created**: YYYY-MM-DD
   **Assigned**: {Name or Unassigned}

   ## Description
   {Clear description of the issue or feature request}

   ## Problem
   {What problem does this address?}

   ## Proposed Solution
   {How to solve it}

   ## Acceptance Criteria
   - [ ] Criterion 1
   - [ ] Criterion 2

   ## Dependencies
   {Related issues or external dependencies}
   ```

5. **Updating Status**: When status changes, rename the file to reflect new status
   - Example: `001-open-user-scoring.md` → `001-in-progress-user-scoring.md`

6. **Location**: All issues are stored in `issues/` directory

#### Completed Issues
- [#001](issues/001-completed-user-scoring-learning.md): ✅ User scoring and learning system (Completed: Oct 4, 2025)
- [#002](issues/002-completed-highlight-full-content.md): ✅ Highlight search terms in full content (Completed: Oct 3, 2025)

#### Current Open Issues
- [#003](issues/003-open-ui-model-filter.md): Add general client-side filter mechanism to search UI (Priority: Medium)
- [#004](issues/004-open-learning-to-rank.md): Implement Learning to Rank (LTR) architecture (Priority: Low - Future Enhancement)

### Running the Application
```bash
# Start Elasticsearch (Docker Compose)
docker-compose up -d

# Run FastAPI application
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Access the application
# - Search UI: http://localhost:8000/
# - API Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
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
├── docker-compose.yml     # Elasticsearch container setup
│
├── docs/                  # Documentation
│   ├── context_session.md
│   ├── technical_design_document.md
│   ├── pitch-personalization-guide.md
│   └── API.md
│
├── tasks/                 # Planning documents
│   ├── prd-document-search-system.md
│   ├── prd-mcp-server-transformation.md
│   └── tasks-prd-document-search-system.md
│
├── scripts/               # Utility scripts
│   ├── add_feedback_table.py
│   └── record_demo.py    # Playwright demo video recording
│
├── static/                # Frontend assets
│   ├── index.html        # Search UI (HTML/CSS/JS)
│   ├── pitch.html        # Pitch presentation with personalization
│   └── demo.webm         # Demo video recording
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
├── tests/                # Test files (83 passing)
│   ├── conftest.py
│   ├── test_pdf_parser.py
│   ├── test_summarizer.py
│   ├── test_document_processor.py
│   ├── test_search_service.py
│   ├── test_api_documents.py
│   ├── test_api_search.py
│   └── test_e2e_user_flow.py
│
└── data/                 # Runtime data
    └── pdfs/            # Uploaded PDF storage
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
- **Highlighting**: Extract snippets with matched terms (~150 chars)
- **Full Content**: Optional full page content with preserved HTML/table structure
- **Filters**: Category, machine model, date range
- **Performance**: Typical 10-50ms response time (well under 3s target)

### Search UI Features
- **Interactive Interface**: Single-page HTML/CSS/JS at root URL (`/`)
- **Search Options**: Fuzzy matching toggle, highlighting toggle, page size selector
- **Filters**: Category dropdown with dynamic filtering
- **Results Display**:
  - Highlighted snippets with matched terms
  - Expandable full content with "Show/Hide Full Content" button
  - Rendered HTML with proper table formatting
  - Pagination for large result sets
- **Environment Agnostic**: Auto-detects URL (works in localhost, Codespaces, production)

### Performance Metrics (Validated - Oct 3, 2025)

**Processing Times:**
- Document Upload: <1s (target: <5s) ✅
- PDF Parsing (1 page): ~10s (LandingAI dpt-2-latest)
- Summarization (1 page): ~2s (Claude Haiku 3, 3K tokens)
- Elasticsearch Indexing: ~38ms
- **Total Processing (1 page)**: ~12s (target: <30s) ✅

**Search Performance:**
- Response Time: 55ms (target: <3s) ✅
- p95 Latency: <100ms (target: <3s) ✅
- BM25 Relevance Scoring: Working
- Document Download: <1s ✅

**Test Coverage:**
- 83 tests passing (all categories)
- Integration tested with real PDFs

### Cost Structure
- **Elasticsearch**: $0/month (Basic tier free for self-managed)
- **LandingAI**: ~$0.01-0.05 per page (estimate, rate limits apply)
- **Claude Haiku 3**: $0.0037 per document (validated with real usage)
- **Infrastructure**: ~$75-300/month (server/VM)
- **Total MVP**: ~$75/month operational costs

### Known Limitations (Discovered Oct 3, 2025)
- **LandingAI**: 50-page maximum per PDF (hard limit)
- **LandingAI**: Rate limiting on API calls (429 errors)
- **Solution**: Implement PDF chunking for large documents + retry logic
- **Impact**: Large technical manuals (>50 pages) require pre-processing

## API Endpoints

### Search (✅ Implemented)
- `POST /api/v1/search` - Search documents with multi-field queries, fuzzy matching, filters, highlighting
  - Query parameters: `query`, `filters`, `page`, `page_size`, `enable_fuzzy`, `include_highlights`, `include_content`
  - Returns: Paginated results with snippets, scores, metadata, and optional full content

### Health (✅ Implemented)
- `GET /health` - Health check endpoint
- `GET /` - Serves search UI (HTML interface)
- `GET /pitch.html` - Serves pitch presentation page with personalization support

### Document Management (✅ Implemented)
- `POST /api/v1/documents/upload` - Upload PDF document with metadata (requires API key)
  - Accepts: multipart/form-data (PDF file + category + machine_model)
  - Validates: file type (PDF only), file size (max 100MB)
  - Returns: 202 Accepted with document_id
  - Triggers: background processing task
- `GET /api/v1/documents/{id}` - Get document status and metadata (requires API key)
  - Returns: document_id, filename, status, upload_date, total_pages, error_message
- `GET /api/v1/documents` - List documents with pagination and filters (requires API key)
  - Query params: status, category, page, page_size
  - Returns: paginated list with total count
- `DELETE /api/v1/documents/{id}` - Delete document and all associated data (requires API key)
  - Deletes: database record, PDF file, Elasticsearch index entries
  - Returns: 204 No Content
- `GET /api/v1/documents/{id}/download` - Download original PDF (requires API key)
  - Returns: PDF file with proper content-disposition header

### Feedback System (✅ Implemented - Issue #001)
- `POST /api/v1/feedback` - Submit user feedback for search results (no authentication required)
  - Body: `{query, document_id, page, rating, session_id?}`
  - Rating: `positive` or `negative` (thumbs up/down)
  - Session ID: Optional anonymous session tracking
  - Returns: Feedback confirmation with feedback_id
  - **Effect**: Invalidates cache and affects future search rankings
- `GET /api/v1/feedback/stats/{document_id}/{page}` - Get feedback statistics (admin endpoint)
  - Returns: `{positive_count, negative_count, total_count, boost_score}`
  - Boost score: 1.0 = neutral, >1.0 = boost, <1.0 = penalty
  - Formula: `boost = 1.0 + (positive_count - negative_count) * 0.1`

**Feedback Features**:
- ✅ Thumbs up/down UI buttons on each search result
- ✅ Anonymous voting with session tracking (sessionStorage)
- ✅ One vote per result per session (prevents duplicate votes)
- ✅ Real-time score boosting (10% per net positive vote)
- ✅ 5-minute cache with automatic invalidation
- ✅ PostgreSQL storage with indexed queries
- ✅ Affects search ranking immediately after submission

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
