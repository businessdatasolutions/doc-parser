# Document Search & Retrieval System

AI-powered document search system for sales department to quickly find information in PDF documentation (maintenance manuals, operation instructions, spare parts catalogs).

**Performance**: Reduces search time from 30 minutes to <3 minutes (90% improvement)

## Features

- **Fast Full-Text Search**: BM25 algorithm with fuzzy matching for typos
- **Intelligent PDF Processing**: Automatic parsing with table/structure preservation
- **AI Summarization**: Claude Haiku 3 generates concise page summaries
- **Multi-Field Search**: Search across content, summaries, part numbers, machine models
- **Advanced Filtering**: Filter by category, machine model, date range
- **User Feedback & Learning**: Thumbs up/down rating system that improves search rankings
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

### User Feedback System

The system includes a user feedback mechanism that learns from user interactions to improve search result rankings over time.

#### How It Works

1. **User Rates Results**: Users click 👍 (helpful) or 👎 (not helpful) on search results
2. **Feedback Stored**: Ratings are stored in PostgreSQL with the search query, document, and page number
3. **Score Boosting Applied**: Search results are re-ranked based on historical feedback
4. **Continuous Learning**: The more users rate results, the better the search becomes

#### Feedback Algorithm

**Simple Score Boosting**:
```
boost_score = 1.0 + (positive_votes - negative_votes) × 0.1
final_score = base_BM25_score × boost_score
```

**Example**:
- 3 positive votes, 1 negative vote = net +2 votes
- Boost score = 1.0 + (2 × 0.1) = 1.2 (20% boost)
- If base score = 7.5, final score = 7.5 × 1.2 = 9.0

**Clamping**: Boost scores are clamped to range 0.1 - 3.0 to prevent extreme distortion.

#### Using Feedback in the UI

1. Search for something (e.g., "motor replacement")
2. Review the results
3. Click 👍 on helpful results or 👎 on unhelpful results
4. Buttons will highlight and disable after voting
5. Search again - positively-rated results will rank higher

**Session Tracking**: The UI uses sessionStorage to track votes, preventing duplicate ratings in the same browser session.

#### Using Feedback via API

**Submit Feedback**:
```bash
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "motor replacement",
    "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
    "page": 15,
    "rating": "positive",
    "session_id": "user_session_abc123"
  }'
```

Response:
```json
{
  "feedback_id": "f7a8b9c0-1234-5678-90ab-cdef12345678",
  "query": "motor replacement",
  "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
  "page": 15,
  "rating": "positive",
  "timestamp": "2025-10-04T10:30:00Z",
  "message": "Feedback submitted successfully"
}
```

**Get Feedback Statistics**:
```bash
curl "http://localhost:8000/api/v1/feedback/stats/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e/15"
```

Response:
```json
{
  "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
  "page": 15,
  "positive_count": 5,
  "negative_count": 1,
  "total_count": 6,
  "boost_score": 1.4
}
```

#### Feedback Data Model

```
search_feedback table:
├── id (UUID)
├── query (TEXT) - The search query
├── document_id (UUID) - Foreign key to documents
├── page (INTEGER) - Page number
├── rating (VARCHAR) - 'positive' or 'negative'
├── session_id (VARCHAR) - Optional anonymous session ID
├── timestamp (TIMESTAMP)
└── created_at (TIMESTAMP)

Indexes:
- (document_id, page) - Fast lookup for boost scores
- query - Analytics on popular queries
- timestamp - Time-based analysis
```

#### Performance Optimization

**5-Minute Cache**: Feedback boost scores are cached in memory for 5 minutes to reduce database queries. The cache is automatically invalidated when new feedback is submitted.

```python
# Cache hit rate: ~95% after warm-up
# Average lookup time: <1ms (cached) vs ~10ms (database)
```

#### Privacy & Security

- **No Authentication Required**: Users can submit feedback anonymously
- **Session Tracking**: Optional session_id for analytics without user identification
- **No PII Collected**: Only query text, document reference, and rating stored
- **CASCADE Deletion**: Feedback is automatically deleted when documents are removed

#### Use Cases

**Continuous Improvement**:
- Sales agents rate helpful results positively
- Unhelpful or irrelevant results get negative ratings
- Future searches automatically benefit from collective knowledge

**Quality Monitoring**:
- Check feedback stats to identify problematic documents
- Monitor which queries get consistently poor ratings
- Identify documents that need better indexing or metadata

**A/B Testing** (Future Enhancement):
- Compare search algorithms by analyzing feedback metrics
- Measure impact of ranking changes on user satisfaction

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
│   │   ├── search.py      # Search endpoints
│   │   └── feedback.py    # Feedback endpoints
│   │
│   ├── models/            # Pydantic schemas
│   │   ├── document.py
│   │   ├── search.py
│   │   └── feedback.py    # Feedback models
│   │
│   ├── services/          # Business logic
│   │   ├── pdf_parser.py
│   │   ├── summarizer.py
│   │   ├── document_processor.py
│   │   └── search_service.py  # Includes feedback boosting
│   │
│   ├── db/                # Database clients
│   │   ├── elasticsearch.py
│   │   └── postgres.py    # Includes Feedback model
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

**Test Coverage**: 114 tests, all passing (including large PDF processing tests)

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

**Version**: 1.1.0
**Last Updated**: October 4, 2025
**Status**: Production-ready with learning capabilities
