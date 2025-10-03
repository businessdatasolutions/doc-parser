# Task List: Document Search & Retrieval System

**Based on:** [prd-document-search-system.md](./prd-document-search-system.md)
**Technical Design:** [technical_design_document.md](../docs/technical_design_document.md)
**Created:** October 2, 2025
**Status:** Ready for Implementation

---

## Relevant Files

### Configuration Files
- `.env` - Environment variables (API keys, Elasticsearch credentials)
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore patterns
- `pytest.ini` - Pytest configuration

### Application Code
- `src/main.py` - FastAPI application entry point
- `src/config.py` - Configuration management and validation
- `src/api/documents.py` - Document upload/management endpoints
- `src/api/search.py` - Search endpoints
- `src/models/document.py` - Document Pydantic schemas
- `src/models/search.py` - Search request/response schemas
- `src/services/pdf_parser.py` - LandingAI PDF parsing integration
- `src/services/summarizer.py` - Claude Haiku 3 summarization
- `src/services/document_processor.py` - Document processing pipeline
- `src/services/search_service.py` - Elasticsearch search queries
- `src/db/elasticsearch.py` - Elasticsearch client and index management
- `src/db/postgres.py` - PostgreSQL database connection
- `src/utils/logging.py` - Logging configuration
- `src/utils/auth.py` - API key authentication middleware

### Testing Files
- `tests/conftest.py` - Pytest fixtures and test configuration
- `tests/test_pdf_parser.py` - PDF parser unit tests
- `tests/test_summarizer.py` - Summarizer unit tests
- `tests/test_document_processor.py` - Processing pipeline tests
- `tests/test_search_service.py` - Search service unit tests
- `tests/test_api_documents.py` - Document API integration tests
- `tests/test_api_search.py` - Search API integration tests
- `tests/test_e2e_user_flow.py` - End-to-end tests

### Documentation
- `docs/API.md` - API documentation
- `README.md` - Project setup and usage guide

---

## Tasks

### Phase 1A: Core MVP (Weeks 1-4)

- [x] **1.0 Project Setup & Infrastructure Configuration**
  - [x] 1.1 Initialize Python project structure with FastAPI
    - Create `src/` directory with `__init__.py`
    - Create subdirectories: `api/`, `models/`, `services/`, `db/`, `utils/`
    - Create `tests/` directory structure
  - [x] 1.2 Create `requirements.txt` with dependencies
    - FastAPI and uvicorn
    - Elasticsearch Python client (8.11+)
    - LandingAI ADE SDK
    - Anthropic Python SDK
    - Python-dotenv, Pydantic, pytest
    - PostgreSQL adapter (psycopg2-binary)
  - [x] 1.3 Configure environment variables in `.env`
    - VISION_AGENT_API_KEY (LandingAI)
    - ANTHROPIC_API_KEY (Claude)
    - ELASTICSEARCH_URL, ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD
    - DATABASE_URL (PostgreSQL)
    - API_KEY (for authentication)
    - PDF_STORAGE_PATH
  - [x] 1.4 Create `src/config.py` for configuration management
    - Load and validate environment variables
    - Define configuration classes using Pydantic
    - Export config singleton
  - [x] 1.5 Set up logging configuration in `src/utils/logging.py`
    - Configure structured logging with JSON format
    - Set log levels based on environment
    - Add request ID tracking
  - [x] 1.6 Create `src/main.py` FastAPI application entry point
    - Initialize FastAPI app
    - Configure CORS middleware
    - Add health check endpoint (`/health`)
    - Add API versioning (`/api/v1/`)
  - [x] 1.7 Create `.gitignore` file
    - Ignore `.env`, `.myenv/`, `__pycache__/`, `.pytest_cache/`
    - Ignore uploaded PDFs directory
  - [x] 1.8 Create `pytest.ini` for test configuration
    - Configure test paths and options
    - Set up test markers (unit, integration, e2e)

- [x] **2.0 Elasticsearch Setup & Index Configuration**
  - [x] 2.1 Create Docker Compose configuration for services
    - Create `docker-compose.yml` with Elasticsearch 8.11.0 and PostgreSQL 14
    - Configure Elasticsearch (single-node, security disabled for dev)
    - Configure PostgreSQL with dev credentials
    - Add volume mounts for data persistence
    - Create `scripts/start_services.sh` helper script
  - [x] 2.2 Start services with Docker Compose and verify
    - Run `docker-compose up -d`
    - Verify Elasticsearch is accessible on http://localhost:9200
    - Verify PostgreSQL is accessible on localhost:5432
    - Test Elasticsearch cluster health
  - [x] 2.3 Create `src/db/elasticsearch.py` client module
    - Initialize Elasticsearch client with connection pooling
    - Implement health check function
    - Add retry logic and error handling
  - [x] 2.4 Implement `documents` index schema creation
    - Define index settings (shards, replicas, analyzers)
    - Define mappings (document_id, filename, content, summary, etc.)
    - Implement index creation function with idempotency
  - [x] 2.5 Write tests for Elasticsearch connection
    - Test connection health check
    - Test index creation
    - Test document indexing and retrieval

- [x] **3.0 Core Document Processing Pipeline**
  - [x] 3.1 Create `src/models/document.py` Pydantic schemas
    - DocumentUploadRequest (category, machine_model, metadata)
    - DocumentUploadResponse (document_id, status)
    - DocumentMetadata (filename, file_size, upload_date)
    - ProcessingStatus enum (uploaded, parsing, summarizing, indexing, ready, failed)
  - [x] 3.2 Implement `src/services/pdf_parser.py` LandingAI integration
    - Initialize LandingAI client
    - Implement `parse_pdf(file_path: Path) -> str` function
    - Parse PDF to markdown using `dpt-2-latest` model
    - Handle parsing errors with retry logic
    - Add logging for parsing metrics
  - [x] 3.3 Implement markdown chunking by page
    - Parse markdown to extract page boundaries
    - Split content into page-level chunks
    - Preserve structure (headers, tables, lists)
    - Extract metadata (page numbers, sections)
  - [x] 3.4 Create `src/services/summarizer.py` Claude integration
    - Initialize Anthropic client
    - Implement `summarize_text(content: str) -> str` function
    - Use Claude Haiku 3 model (`claude-3-haiku-20240307`)
    - Optimize prompt for technical document summaries
    - Handle rate limiting and errors
  - [x] 3.5 Implement `src/services/document_processor.py` pipeline
    - Orchestrate: save PDF → parse → chunk → summarize → index
    - Update processing status at each stage
    - Implement error handling and rollback
    - Add progress tracking
  - [x] 3.6 Create `src/db/postgres.py` for metadata storage
    - Define documents table schema (id, filename, status, timestamps)
    - Implement CRUD operations
    - Add connection pooling
  - [x] 3.7 Write unit tests for processing pipeline
    - Test PDF parsing with sample document
    - Test chunking logic
    - Test summarization with mock API
    - Test full pipeline with integration test

- [x] **4.0 Search API Implementation**
  - [x] 4.1 Create `src/models/search.py` Pydantic schemas
    - SearchRequest (query, filters, pagination)
    - SearchResponse (results, total, took)
    - SearchResult (document_id, filename, page, snippet, score)
    - SearchFilters (category, machine_model, date_range)
  - [x] 4.2 Implement `src/services/search_service.py` Elasticsearch queries
    - Build multi-match query with BM25
    - Implement fuzzy matching (`fuzziness: "AUTO"`)
    - Add field boosting (content^2, summary^1.5, part_numbers^3)
    - Implement highlighting for matched terms
  - [x] 4.3 Add pagination support
    - Implement `from` and `size` parameters
    - Default page size: 10, max: 100
    - Return total count and page metadata
  - [x] 4.4 Implement search filters
    - Filter by category (maintenance, operations, spare_parts)
    - Filter by machine_model (keyword match)
    - Filter by date_range (upload_date)
    - Combine filters with bool query
  - [x] 4.5 Create `src/api/search.py` search endpoint
    - POST `/api/v1/search` endpoint
    - Validate request with Pydantic
    - Call search service
    - Return formatted results with snippets
    - Add request/response logging
  - [x] 4.6 Add search result snippet generation
    - Extract highlighted text around matches
    - Limit snippet length (200 chars)
    - Add ellipsis (...) for truncated text
  - [x] 4.7 Implement aggregations for faceted search
    - Aggregate by category (count per category)
    - Aggregate by machine_model
    - Return facets in search response
  - [x] 4.8 Write unit tests for search service
    - Test query building with various parameters
    - Test fuzzy matching with typos
    - Test filtering logic
    - Test pagination
  - [x] 4.9 Write integration tests for search API
    - Index sample documents
    - Test search with various queries
    - Test filters and pagination
    - Test error handling (invalid queries)

- [x] **5.0 Document Management API**
  - [x] 5.1 Create `src/utils/auth.py` API key authentication
    - Implement API key middleware
    - Validate Authorization header
    - Return 401 for invalid/missing keys
  - [x] 5.2 Implement POST `/api/v1/documents/upload` endpoint
    - Accept multipart/form-data (PDF file + metadata)
    - Validate file type (PDF only)
    - Validate file size (max 100MB)
    - Save PDF to storage path
    - Create database record with status "uploaded"
    - Trigger background processing task
    - Return 202 Accepted with document_id
  - [x] 5.3 Implement GET `/api/v1/documents/{document_id}` endpoint
    - Retrieve document metadata from database
    - Return status, filename, upload_date, etc.
    - Return 404 if document not found
  - [x] 5.4 Implement GET `/api/v1/documents` list endpoint
    - Support pagination (page, page_size)
    - Support filtering by status
    - Support sorting by upload_date
    - Return list of documents with metadata
  - [x] 5.5 Implement DELETE `/api/v1/documents/{document_id}` endpoint
    - Delete document from database
    - Delete PDF file from storage
    - Delete all pages from Elasticsearch index
    - Return 204 No Content on success
  - [x] 5.6 Implement GET `/api/v1/documents/{document_id}/download` endpoint
    - Stream PDF file to client
    - Set Content-Disposition header
    - Handle missing files gracefully
  - [x] 5.7 Add background task processing with FastAPI BackgroundTasks
    - Process documents asynchronously after upload
    - Update status in database during processing
    - Handle failures and update status to "failed"
  - [x] 5.8 Write integration tests for document API
    - Test upload with valid PDF
    - Test upload with invalid file (non-PDF, oversized)
    - Test retrieve, list, delete operations
    - Test concurrent uploads

- [ ] **6.0 Testing & Quality Assurance**
  - [ ] 6.1 Create `tests/conftest.py` with pytest fixtures
    - Elasticsearch test client fixture
    - PostgreSQL test database fixture
    - FastAPI test client fixture
    - Sample PDF fixture
    - Mock LandingAI client fixture
    - Mock Anthropic client fixture
  - [ ] 6.2 Write unit tests for all service modules
    - `test_pdf_parser.py` - Test parsing with sample PDFs
    - `test_summarizer.py` - Test summarization with mocks
    - `test_document_processor.py` - Test pipeline stages
    - `test_search_service.py` - Test query building
  - [ ] 6.3 Write integration tests for API endpoints
    - `test_api_documents.py` - Test document CRUD operations
    - `test_api_search.py` - Test search with real Elasticsearch
  - [ ] 6.4 Write end-to-end test for complete user flow
    - `test_e2e_user_flow.py`
    - Test: Upload → Wait for processing → Search → Retrieve
    - Use real PDF document
    - Verify all stages complete successfully
  - [ ] 6.5 Add performance tests
    - Test search latency (<3s for p95)
    - Test document processing time (<5s per doc)
    - Test concurrent upload handling (10 simultaneous)
  - [ ] 6.6 Achieve minimum test coverage
    - Target: >80% code coverage
    - Run `pytest --cov=src` to measure
    - Add missing tests for uncovered code

- [ ] **7.0 Deployment & Documentation**
  - [ ] 7.1 Create `README.md` with setup instructions
    - Project overview and architecture
    - Prerequisites (Python 3.10+, Elasticsearch 8.11+, PostgreSQL)
    - Installation steps
    - Environment configuration
    - Running the application
    - Running tests
  - [ ] 7.2 Create `docs/API.md` API documentation
    - Document all endpoints with examples
    - Include request/response schemas
    - Add authentication instructions
    - Include error codes and messages
  - [ ] 7.3 Create deployment scripts
    - Script to start Elasticsearch
    - Script to initialize database
    - Script to create Elasticsearch index
    - Script to start FastAPI application
  - [ ] 7.4 Set up Docker Compose (optional)
    - Dockerfile for FastAPI application
    - Docker Compose with Elasticsearch, PostgreSQL, and app
    - Volume mounts for data persistence
  - [ ] 7.5 Create sample data loading script
    - Script to upload 10-20 sample PDFs
    - Verify all documents process successfully
    - Test search functionality with sample data
  - [ ] 7.6 Final integration testing
    - Run full test suite
    - Test with real documents
    - Verify all acceptance criteria from PRD

### Phase 1B: Enhanced Features (Weeks 5-8)

- [ ] **8.0 Advanced Search Features**
  - [ ] 8.1 Implement custom analyzers for technical terms
    - Create technical_analyzer in Elasticsearch
    - Add word_delimiter_graph filter
    - Update index mappings
    - Re-index existing documents
  - [ ] 8.2 Add phrase matching with boosting
    - Implement match_phrase query for exact terms
    - Boost phrase matches 3x
    - Combine with fuzzy matching in bool query
  - [ ] 8.3 Implement aggregations for faceted search UI
    - Add category facets with counts
    - Add machine_model facets
    - Add date histogram aggregations
  - [ ] 8.4 Add search result ranking optimization
    - Tune field boost values based on user feedback
    - Implement custom scoring functions
    - A/B test different ranking strategies

- [ ] **9.0 Monitoring & Optimization**
  - [ ] 9.1 Add application metrics
    - Track search latency (p50, p95, p99)
    - Track document processing time
    - Track API error rates
  - [ ] 9.2 Implement query performance logging
    - Log slow queries (>1s)
    - Track query patterns
    - Identify optimization opportunities
  - [ ] 9.3 Add Elasticsearch index optimization
    - Configure refresh_interval
    - Optimize shard allocation
    - Set up index lifecycle management
  - [ ] 9.4 Implement caching for frequent queries
    - Add Redis for query result caching
    - Cache document summaries
    - Set appropriate TTL values

- [ ] **10.0 Pilot Deployment**
  - [ ] 10.1 Deploy to test/staging environment
    - Set up VM with required specifications
    - Deploy Elasticsearch cluster
    - Deploy FastAPI application
    - Configure SSL/TLS certificates
  - [ ] 10.2 Index production document set
    - Upload 100-500 real documents
    - Monitor processing pipeline
    - Verify search quality
  - [ ] 10.3 Conduct pilot with sales team
    - Onboard 5 sales agents
    - Provide training and documentation
    - Collect feedback on search quality
    - Track usage metrics
  - [ ] 10.4 Iterate based on feedback
    - Prioritize improvements based on user feedback
    - Fix bugs and usability issues
    - Optimize search relevance
    - Prepare for production rollout

---

## Implementation Notes

### Task Execution Protocol
1. **One sub-task at a time** - Complete each sub-task fully before moving to the next
2. **Mark completed** - Change `[ ]` to `[x]` when sub-task is done
3. **Test after parent task** - Run full test suite when all sub-tasks under a parent are complete
4. **Commit after parent task** - Stage changes, clean up, and commit with descriptive message
5. **Wait for approval** - Ask user for permission before starting next sub-task

### Commit Message Format
Use conventional commit format with multiple `-m` flags:
```bash
git commit -m "feat: implement PDF parsing service" \
  -m "- Integrate LandingAI ADE SDK" \
  -m "- Add error handling and retry logic" \
  -m "- Includes unit tests" \
  -m "Completes task 3.2 from PRD"
```

### Testing Requirements
- Run `pytest` after completing each parent task
- Ensure all tests pass before committing
- Maintain >80% code coverage
- Fix any test failures before proceeding

---

**Current Status:** Ready to begin Task 1.1
**Next Action:** Awaiting user approval to start implementation
