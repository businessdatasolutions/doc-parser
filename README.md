# Document Search & Retrieval System

AI-powered document search system for sales department to quickly find information in PDF documentation (maintenance manuals, operation instructions, spare parts catalogs).

**Performance**: Reduces search time from 30 minutes to <3 minutes (90% improvement)

## Features

- **Fast Full-Text Search**: BM25 algorithm with fuzzy matching for typos
- **Intelligent PDF Processing**: Automatic parsing with table/structure preservation
- **AI Summarization**: Claude Haiku 3 generates concise page summaries
- **Multi-Field Search**: Search across content, summaries, part numbers, machine models
- **Advanced Filtering**: Filter by category, machine model, date range
- **Interactive Web UI**: Clean search interface with highlighting and full content display
- **RESTful API**: Complete document management and search endpoints
- **Page Limiting**: Automatic handling of large PDFs (>50 pages) with transparent truncation

## Architecture

```
┌─────────────┐
│   User/UI   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│      FastAPI Backend            │
│  ┌──────────┬────────────────┐  │
│  │ Document │    Search      │  │
│  │   API    │     API        │  │
│  └────┬─────┴────────┬───────┘  │
│       │              │          │
│  ┌────▼──────┐  ┌────▼──────┐  │
│  │ Document  │  │  Search   │  │
│  │ Processor │  │  Service  │  │
│  └────┬──────┘  └────┬──────┘  │
└───────┼──────────────┼─────────┘
        │              │
   ┌────▼──────┐  ┌────▼──────────┐
   │ LandingAI │  │ Elasticsearch │
   │   (PDF)   │  │     (BM25)    │
   └───────────┘  └───────────────┘
        │
   ┌────▼──────┐
   │  Claude   │
   │ Haiku 3   │
   └───────────┘
```

### Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **Search Engine**: Elasticsearch 8.11+ (BM25 full-text search)
- **PDF Parsing**: LandingAI ADE SDK (`dpt-2-latest` model)
- **Summarization**: Claude Haiku 3 (`claude-3-haiku-20240307`)
- **Database**: PostgreSQL 14+ (document metadata)
- **Testing**: pytest (90 tests, 77% coverage)

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for Elasticsearch and PostgreSQL)
- LandingAI API key ([sign up here](https://landing.ai/))
- Anthropic API key ([sign up here](https://console.anthropic.com/))

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd doc-parser
```

### 2. Create Virtual Environment

```bash
python -m venv .myenv
source .myenv/bin/activate  # On Windows: .myenv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys
VISION_AGENT_API_KEY=your_landingai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme

# PostgreSQL Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/docsearch

# Application Settings
API_KEY=your_secure_api_key_here
PDF_STORAGE_PATH=./data/pdfs
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100

# Optional Settings
CORS_ORIGINS=["*"]
ENVIRONMENT=development
```

### 5. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- Elasticsearch on `http://localhost:9200`
- PostgreSQL on `localhost:5432`

Verify services are running:

```bash
# Check Elasticsearch
curl http://localhost:9200

# Check PostgreSQL (requires psql)
psql postgresql://postgres:postgres@localhost:5432/docsearch -c "SELECT version();"
```

### 6. Initialize Database

The application will automatically create the Elasticsearch index and PostgreSQL tables on first run.

### 7. Run the Application

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- **Search UI**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Usage

### Using the Web Interface

1. Open http://localhost:8000/ in your browser
2. Enter your search query (e.g., "motor replacement procedure")
3. Toggle fuzzy matching for typo tolerance
4. Use category filters to narrow results
5. Click "Show Full Content" to view complete page content with tables

### Using the API

#### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer your_secure_api_key_here" \
  -F "file=@/path/to/document.pdf" \
  -F "category=maintenance" \
  -F "machine_model=AGV-2000"
```

Response:
```json
{
  "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
  "filename": "document.pdf",
  "status": "uploaded",
  "upload_date": "2025-10-03T10:30:00Z"
}
```

#### Check Document Status

```bash
curl -X GET "http://localhost:8000/api/v1/documents/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e" \
  -H "Authorization: Bearer your_secure_api_key_here"
```

Response:
```json
{
  "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
  "filename": "document.pdf",
  "status": "ready",
  "upload_date": "2025-10-03T10:30:00Z",
  "indexed_at": "2025-10-03T10:31:15Z",
  "total_pages": 42,
  "error_message": null
}
```

**Note**: If your PDF has more than 50 pages, the system will automatically truncate it to 50 pages (LandingAI limitation). You'll see a note in `error_message`:
```json
{
  "error_message": "Note: Original PDF had 164 pages, processed first 50 pages only"
}
```

#### Search Documents

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "motor replacement",
    "enable_fuzzy": true,
    "include_highlights": true,
    "page": 1,
    "page_size": 10,
    "filters": {
      "category": "maintenance"
    }
  }'
```

Response:
```json
{
  "results": [
    {
      "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
      "filename": "maintenance_manual.pdf",
      "page_number": 15,
      "content_snippet": "To perform <em>motor replacement</em>, first disconnect power...",
      "score": 12.45,
      "category": "maintenance",
      "machine_model": "AGV-2000"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "took_ms": 55
}
```

#### List Documents

```bash
curl -X GET "http://localhost:8000/api/v1/documents?status=ready&page=1&page_size=10" \
  -H "Authorization: Bearer your_secure_api_key_here"
```

#### Download Document

```bash
curl -X GET "http://localhost:8000/api/v1/documents/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e/download" \
  -H "Authorization: Bearer your_secure_api_key_here" \
  --output document.pdf
```

#### Delete Document

```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e" \
  -H "Authorization: Bearer your_secure_api_key_here"
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e          # End-to-end tests only

# Run specific test file
pytest tests/test_api_search.py -v
```

### Project Structure

```
doc-parser/
├── .env                    # Environment variables (git-ignored)
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Elasticsearch + PostgreSQL setup
│
├── src/                    # Application code
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Configuration management
│   │
│   ├── api/               # API routes
│   │   ├── documents.py   # Document management endpoints
│   │   └── search.py      # Search endpoints
│   │
│   ├── models/            # Pydantic schemas
│   │   ├── document.py
│   │   └── search.py
│   │
│   ├── services/          # Business logic
│   │   ├── pdf_parser.py
│   │   ├── summarizer.py
│   │   ├── document_processor.py
│   │   └── search_service.py
│   │
│   ├── db/                # Database clients
│   │   ├── elasticsearch.py
│   │   └── postgres.py
│   │
│   └── utils/             # Utilities
│       ├── logging.py
│       ├── auth.py
│       └── pdf_utils.py   # PDF page limiting utilities
│
├── tests/                 # Test files (90 tests, 77% coverage)
│   ├── conftest.py
│   ├── test_pdf_parser.py
│   ├── test_summarizer.py
│   ├── test_document_processor.py
│   ├── test_search_service.py
│   ├── test_api_documents.py
│   ├── test_api_search.py
│   ├── test_pdf_utils.py
│   └── test_e2e_user_flow.py
│
├── static/                # Frontend assets
│   └── index.html         # Search UI
│
└── data/                  # Runtime data
    └── pdfs/              # Uploaded PDF storage
```

## Performance Metrics

**Validated with real documents** (October 3, 2025):

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Document Upload | <5s | <1s | ✅ |
| PDF Parsing (1 page) | <30s | ~10s | ✅ |
| Summarization (1 page) | <30s | ~2s | ✅ |
| Total Processing (1 page) | <30s | ~12s | ✅ |
| Search Response Time | <3s | 55ms | ✅ |
| p95 Search Latency | <3s | <100ms | ✅ |
| Document Download | <5s | <1s | ✅ |

**Test Coverage**: 90 tests, 77% overall coverage

## Known Limitations

### LandingAI 50-Page Limit

LandingAI has a hard limit of 50 pages per PDF document. The system automatically handles this:

1. **Automatic Detection**: When you upload a PDF, the system checks page count
2. **Automatic Truncation**: PDFs >50 pages are truncated to first 50 pages
3. **User Notification**: The `error_message` field notifies you of truncation:
   ```json
   "error_message": "Note: Original PDF had 164 pages, processed first 50 pages only"
   ```
4. **Temporary Files**: Limited PDFs are cleaned up after processing

**Workaround for large documents**: Split your PDF into multiple 50-page chunks before uploading.

### Rate Limiting

LandingAI API has rate limits. If you encounter 429 errors:
- Wait a few minutes between uploads
- Process documents sequentially rather than in parallel

## Cost Estimates

**MVP Monthly Costs** (based on usage testing):

- **Elasticsearch**: $0/month (Basic tier free for self-managed)
- **LandingAI**: ~$0.01-0.05 per page
- **Claude Haiku 3**: ~$0.0037 per document
- **Infrastructure**: ~$75-300/month (VM/server)

**Total**: ~$75/month operational costs (infrastructure only) + per-document processing fees

## Troubleshooting

### Elasticsearch Connection Failed

```bash
# Check if Elasticsearch is running
docker ps | grep elasticsearch

# Check Elasticsearch logs
docker logs doc-parser-elasticsearch-1

# Restart Elasticsearch
docker-compose restart elasticsearch
```

### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs doc-parser-postgres-1

# Restart PostgreSQL
docker-compose restart postgres
```

### Document Processing Stuck

Check document status:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/{document_id}" \
  -H "Authorization: Bearer your_api_key"
```

If status is stuck in `parsing` or `uploaded`:
1. Check application logs for errors
2. Verify LandingAI API key is valid
3. Verify Anthropic API key is valid
4. Check for rate limiting (429 errors)

### Tests Failing

```bash
# Ensure services are running
docker-compose up -d

# Clear test cache
pytest --cache-clear

# Run tests with verbose output
pytest -v --tb=short
```

## API Documentation

For complete API documentation with request/response schemas, visit:
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **API Reference**: [docs/API.md](docs/API.md)

## Contributing

1. Follow the task list in [tasks/tasks-prd-document-search-system.md](tasks/tasks-prd-document-search-system.md)
2. Write tests for all new code (target >80% coverage)
3. Use type hints and docstrings
4. Run `pytest` before committing
5. Use conventional commit format

## Security Notes

- **Never commit `.env` file** - Contains API keys and secrets
- **API Key Required** - All document management endpoints require authentication
- **Input Validation** - All user inputs are validated
- **File Size Limits** - PDFs are limited to 100MB by default
- **SQL Injection Protection** - Uses parameterized queries

## License

[Your License Here]

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Version**: 1.0.0
**Last Updated**: October 3, 2025
**Status**: Production-ready MVP
