# Technical Design Document: Document Search & Retrieval System

**Version:** 1.1
**Date:** October 2, 2025
**Status:** Final (Enhanced with Elasticsearch best practices)
**Author:** Tech Lead / Architecture Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Data Models](#data-models)
5. [API Design](#api-design)
6. [Document Processing Pipeline](#document-processing-pipeline)
7. [Search Implementation](#search-implementation)
8. [Infrastructure & Deployment](#infrastructure--deployment)
9. [Security](#security)
10. [Performance](#performance)
11. [Code Organization](#code-organization)
12. [Testing Strategy](#testing-strategy)
13. [Development Phases](#development-phases)
14. [Risks & Mitigations](#risks--mitigations)
15. [Future Enhancements](#future-enhancements)

---

## Executive Summary

### Purpose
Design and implement a document search and retrieval system to help the internal sales department quickly find information in PDF documentation, reducing search time from 30 minutes to <3 minutes (90% improvement).

### Key Design Decisions
- **Architecture:** Simple, proven stack leveraging existing Elasticsearch patterns
- **Search:** Elasticsearch BM25 full-text search (no vector embeddings for MVP)
- **Parsing:** LandingAI ADE SDK (already validated with sample documents)
- **Summarization:** Claude Haiku 3 (cost-effective at $0.25/$1.25 per MTok)
- **Deployment:** Start with single-node Elasticsearch, scale as needed
- **Licensing:** Elasticsearch Basic (Free) - includes all required search features

### Success Criteria
- Search response time <3 seconds (p95)
- Document indexing <5 seconds per document
- Search accuracy >90% (relevant results in top 5)
- Support 10,000 documents initially, scalable to 100,000

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                        │
│                    (Web UI / API Clients)                     │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────┴──────────────────────────────────┐
│                      REST API LAYER                           │
│         (FastAPI / Flask - Python Backend)                    │
│                                                               │
│  Endpoints:                                                   │
│  - POST /api/v1/documents/upload                             │
│  - POST /api/v1/search                                       │
│  - GET  /api/v1/documents/{id}                              │
│  - GET  /api/v1/documents                                    │
└───┬────────────────┬──────────────────────┬──────────────────┘
    │                │                      │
    │                │                      │
    ▼                ▼                      ▼
┌────────┐   ┌──────────────┐      ┌──────────────┐
│  File  │   │  LandingAI   │      │   Anthropic  │
│Storage │   │  ADE SDK     │      │   Claude     │
│(Local/ │   │ (PDF Parser) │      │   Haiku 3    │
│ S3)    │   │              │      │(Summarizer)  │
└────────┘   └──────────────┘      └──────────────┘
    │                │                      │
    └────────────────┴──────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   ELASTICSEARCH       │
         │   (Search & Storage)  │
         │                       │
         │  - Index: documents   │
         │  - BM25 Search        │
         │  - Highlighting       │
         │  - Aggregations       │
         └───────────────────────┘
```

### Component Responsibilities

#### 1. REST API Layer
- **Technology:** FastAPI (Python)
- **Responsibilities:**
  - Handle HTTP requests/responses
  - Authentication and authorization
  - Input validation and sanitization
  - Orchestrate document processing pipeline
  - Query Elasticsearch for search
  - Return formatted results

#### 2. Document Processing Service
- **Responsibilities:**
  - Validate uploaded PDFs
  - Call LandingAI ADE SDK for parsing
  - Extract markdown from parse response
  - Call Claude Haiku 3 for summarization
  - Chunk markdown content (by page/section)
  - Index content in Elasticsearch
  - Handle errors and retries

#### 3. Elasticsearch Cluster
- **Responsibilities:**
  - Store indexed document content
  - Store metadata (filename, category, machine_model, date)
  - Execute BM25 full-text search queries
  - Apply filters (category, machine_model, date range)
  - Highlight matching terms
  - Aggregate results for faceted search

#### 4. File Storage
- **Responsibilities:**
  - Store original PDF files
  - Serve files for download
  - Support local filesystem or S3-compatible storage

#### 5. External APIs
- **LandingAI ADE SDK:** PDF → Markdown parsing
- **Anthropic Claude API:** Markdown → Summary generation

### Data Flow

#### Document Upload Flow
```
User → API (upload) → Validate PDF → Store PDF →
LandingAI Parse → Extract Markdown → Claude Summarize →
Chunk Content → Index in Elasticsearch → Return Document ID
```

#### Search Flow
```
User → API (search) → Build ES Query → Elasticsearch Search →
Highlight Results → Format Response → Return JSON
```

#### Document Retrieval Flow
```
User → API (get document) → Query ES by doc_id →
Retrieve all pages → Format markdown → Return with metadata
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| **Backend Framework** | FastAPI | 0.104+ | Fast, modern, async support, auto API docs |
| **Search Engine** | Elasticsearch | 8.11+ | Proven BM25 search, free self-managed, existing patterns to reuse |
| **PDF Parser** | LandingAI ADE SDK | Latest | Already validated, excellent quality |
| **Summarization** | Claude Haiku 3 | 20240307 | Cost-effective ($0.25/$1.25 per MTok) |
| **Language** | Python | 3.10+ | Existing codebase, rich ecosystem |
| **HTTP Client** | httpx | 0.25+ | Async support for external APIs |
| **Environment** | python-dotenv | 1.0+ | Manage API keys securely |

### Infrastructure

| Component | Technology | Configuration |
|-----------|-----------|---------------|
| **Elasticsearch** | Self-hosted (Free/Basic) | Single node (MVP) → 3-node cluster (production) |
| **File Storage** | Local filesystem | MVP: `/data/pdfs/`, Production: S3/Azure Blob |
| **Application Server** | Uvicorn | ASGI server for FastAPI |
| **Database** | Optional PostgreSQL | For user management, audit logs (if needed) |

### Why This Stack?

**Elasticsearch vs Vector Database:**
- ✅ Reuses existing proven patterns (faster development)
- ✅ Excellent for exact matching (part numbers, model names)
- ✅ BM25 is fast and well-understood
- ✅ No GPU requirements
- ✅ **Free self-managed (Basic tier includes BM25, fuzzy matching, highlighting)**
- ✅ Can upgrade to Platinum+ for ELSER semantic search later if needed
- ✅ Mature ecosystem with 74.9k GitHub stars, enterprise-proven

**FastAPI vs Flask:**
- ✅ Modern async/await support
- ✅ Automatic OpenAPI documentation
- ✅ Fast performance
- ✅ Type hints and validation with Pydantic

**Claude Haiku 3 vs Other LLMs:**
- ✅ Most cost-effective ($1.59 per 1K documents)
- ✅ Fast response times
- ✅ 200K context window
- ✅ Good quality for technical summaries
- ✅ Easy upgrade path to Haiku 3.5 if needed

---

## Data Models

### Elasticsearch Index Schema

#### Index: `documents`

```python
{
    "settings": {
        "number_of_shards": 1,        # Single shard for MVP
        "number_of_replicas": 1,      # 1 replica for reliability
        "analysis": {
            "analyzer": {
                "standard": {
                    "type": "standard"
                },
                "part_number_analyzer": {
                    "type": "custom",
                    "tokenizer": "keyword",
                    "filter": ["lowercase"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # Document Identification
            "document_id": {
                "type": "keyword"              # Groups pages from same document
            },
            "filename": {
                "type": "keyword"              # Original filename
            },

            # Content
            "content": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {               # For exact matching
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "summary": {
                "type": "text",
                "analyzer": "standard"
            },

            # Pagination
            "page": {
                "type": "integer"
            },

            # Metadata for Filtering
            "category": {
                "type": "keyword"              # maintenance, operations, spare_parts
            },
            "machine_model": {
                "type": "keyword"              # For filtering by model
            },
            "part_numbers": {
                "type": "keyword",             # Array of part numbers
                "fields": {
                    "analyzed": {
                        "type": "text",
                        "analyzer": "part_number_analyzer"
                    }
                }
            },

            # Timestamps
            "upload_date": {
                "type": "date"
            },
            "indexed_at": {
                "type": "date"
            },

            # File Info
            "file_size": {
                "type": "long"                 # Bytes
            },
            "file_path": {
                "type": "keyword"              # Path to original PDF
            },

            # Processing Status
            "processing_status": {
                "type": "keyword"              # uploaded, parsing, summarizing, indexing, ready, failed
            },
            "error_message": {
                "type": "text"
            }
        }
    }
}
```

### Document Processing States

```python
class ProcessingStatus(Enum):
    UPLOADED = "uploaded"           # PDF received
    PARSING = "parsing"             # LandingAI parsing in progress
    SUMMARIZING = "summarizing"     # Claude summarization in progress
    INDEXING = "indexing"           # Elasticsearch indexing in progress
    READY = "ready"                 # Available for search
    FAILED = "failed"               # Processing error
```

### Document Chunking Strategy

**Approach:** Page-level chunking
- Each Elasticsearch document = 1 page of content
- Same `document_id` links pages from same PDF
- Preserves page numbers for precise citation

**Example:**
```
PDF: "maintenance_manual.pdf" (20 pages)
→ 20 Elasticsearch documents with same document_id
→ Page 1: {"document_id": "abc123", "page": 1, "content": "..."}
→ Page 2: {"document_id": "abc123", "page": 2, "content": "..."}
...
```

**Benefits:**
- Precise page-level results
- Easy to cite source ("found on page 5")
- Natural chunking boundary
- Simple to implement

---

## API Design

### Authentication

**MVP:** Basic API key authentication
```
Authorization: Bearer <api_key>
```

**Production:** Consider OAuth2 or JWT for user-level access control

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. Upload Document

```
POST /api/v1/documents/upload
Content-Type: multipart/form-data
Authorization: Bearer <api_key>

Request:
  file: <binary PDF data>
  category: "maintenance" | "operations" | "spare_parts"
  machine_model: string (optional)
  tags: array of strings (optional)

Response (202 Accepted):
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "conveyor_maintenance.pdf",
  "file_type": "PDF",
  "file_size": 2048576,
  "status": "processing",
  "message": "Document uploaded and processing started",
  "estimated_completion": "2025-10-02T10:15:00Z"
}

Response (400 Bad Request):
{
  "error": "invalid_file_type",
  "message": "Only PDF files are supported"
}

Response (413 Payload Too Large):
{
  "error": "file_too_large",
  "message": "File size exceeds 100MB limit"
}
```

#### 2. Search Documents

```
POST /api/v1/search
Content-Type: application/json
Authorization: Bearer <api_key>

Request:
{
  "query": "conveyor belt replacement Model X2000",
  "filters": {
    "category": ["maintenance", "operations"],      # optional
    "machine_model": ["X2000"],                     # optional
    "date_range": {                                 # optional
      "start": "2024-01-01",
      "end": "2025-10-02"
    }
  },
  "size": 10,                                       # default: 10, max: 50
  "from": 0                                         # pagination offset
}

Response (200 OK):
{
  "results": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "conveyor_maintenance.pdf",
      "page": 12,
      "category": "maintenance",
      "machine_model": "X2000",
      "relevance_score": 15.23,
      "snippet": "...regular <em>belt</em> <em>replacement</em> procedure...",
      "highlights": [
        "The <em>conveyor</em> <em>belt</em> should be inspected monthly",
        "<em>Replacement</em> parts for <em>Model</em> <em>X2000</em> are listed below"
      ],
      "summary": "Maintenance procedures for Model X2000 conveyor system...",
      "upload_date": "2025-09-15T14:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "pages": 5,
  "query_time_ms": 145,
  "facets": {
    "categories": [
      {"name": "maintenance", "count": 25},
      {"name": "operations", "count": 12},
      {"name": "spare_parts", "count": 5}
    ],
    "machine_models": [
      {"name": "X2000", "count": 18},
      {"name": "X3000", "count": 15}
    ]
  }
}
```

#### 3. Get Document

```
GET /api/v1/documents/{document_id}
Authorization: Bearer <api_key>

Query Parameters:
  - include_content: boolean (default: true)
  - page: integer (optional, get specific page only)

Response (200 OK):
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "conveyor_maintenance.pdf",
  "category": "maintenance",
  "machine_model": "X2000",
  "file_size": 2048576,
  "upload_date": "2025-09-15T14:30:00Z",
  "summary": "This document describes maintenance procedures...",
  "total_pages": 20,
  "status": "ready",
  "pages": [
    {
      "page": 1,
      "content": "# Maintenance Manual\n\n## Model X2000..."
    },
    {
      "page": 2,
      "content": "## Safety Procedures..."
    }
  ],
  "download_url": "/api/v1/documents/550e8400-e29b-41d4-a716-446655440000/download"
}

Response (404 Not Found):
{
  "error": "document_not_found",
  "message": "Document with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

#### 4. Download Original PDF

```
GET /api/v1/documents/{document_id}/download
Authorization: Bearer <api_key>

Response (200 OK):
Content-Type: application/pdf
Content-Disposition: attachment; filename="conveyor_maintenance.pdf"
<binary PDF data>
```

#### 5. List Documents

```
GET /api/v1/documents
Authorization: Bearer <api_key>

Query Parameters:
  - status: "ready" | "processing" | "failed" (optional)
  - category: "maintenance" | "operations" | "spare_parts" (optional)
  - page: integer (default: 1)
  - limit: integer (default: 50, max: 100)
  - sort_by: "upload_date" | "filename" (default: "upload_date")
  - sort_order: "asc" | "desc" (default: "desc")

Response (200 OK):
{
  "documents": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "conveyor_maintenance.pdf",
      "category": "maintenance",
      "machine_model": "X2000",
      "file_size": 2048576,
      "upload_date": "2025-09-15T14:30:00Z",
      "status": "ready",
      "total_pages": 20
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 3
}
```

#### 6. Delete Document

```
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <api_key>

Response (200 OK):
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document deleted successfully"
}
```

### Error Responses

All errors follow this format:
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}  // optional additional context
}
```

**Common Error Codes:**
- `invalid_file_type` - Not a PDF
- `file_too_large` - Exceeds 100MB
- `document_not_found` - Invalid document_id
- `processing_failed` - PDF parsing or indexing error
- `invalid_request` - Missing or invalid parameters
- `unauthorized` - Invalid or missing API key
- `rate_limit_exceeded` - Too many requests

---

## Document Processing Pipeline

### Overview

```
Upload → Validate → Store → Parse → Summarize → Chunk → Index → Ready
   ↓         ↓         ↓       ↓         ↓         ↓       ↓
  API     FastAPI   Storage  LandingAI  Claude   Python   ES
```

### Detailed Flow

#### Step 1: Upload & Validation

```python
async def upload_document(
    file: UploadFile,
    category: str,
    machine_model: Optional[str] = None
) -> DocumentResponse:
    """Upload and validate PDF"""

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files accepted")

    # Validate file size
    file_size = await get_file_size(file)
    if file_size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(413, "File too large")

    # Generate document ID
    document_id = str(uuid4())

    # Save to storage
    file_path = await save_file(file, document_id)

    # Create initial index entry
    await create_document_record(
        document_id=document_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        category=category,
        machine_model=machine_model,
        status=ProcessingStatus.UPLOADED
    )

    # Start async processing
    background_tasks.add_task(process_document, document_id)

    return DocumentResponse(
        document_id=document_id,
        filename=file.filename,
        status="processing"
    )
```

#### Step 2: PDF Parsing (LandingAI)

```python
async def parse_pdf(document_id: str, file_path: str) -> str:
    """Parse PDF using LandingAI ADE SDK"""

    try:
        # Update status
        await update_document_status(document_id, ProcessingStatus.PARSING)

        # Initialize client
        client = LandingAIADE(apikey=os.getenv("VISION_AGENT_API_KEY"))

        # Parse PDF
        parse_response = client.parse(
            document=Path(file_path),
            model="dpt-2-latest"
        )

        if not parse_response.markdown:
            raise ValueError("Parsing failed - no markdown output")

        return parse_response.markdown

    except Exception as e:
        await update_document_status(
            document_id,
            ProcessingStatus.FAILED,
            error_message=str(e)
        )
        raise
```

#### Step 3: Summarization (Claude Haiku 3)

```python
async def generate_summary(document_id: str, markdown_content: str) -> str:
    """Generate summary using Claude Haiku 3"""

    try:
        # Update status
        await update_document_status(document_id, ProcessingStatus.SUMMARIZING)

        # Truncate if needed (first 100K characters)
        content_to_summarize = markdown_content[:100000]

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Create prompt
        prompt = f"""Analyze this technical engineering document and provide a concise summary (150-300 words).

Focus on:
1. Document type and purpose
2. Key equipment or machines mentioned (models, part numbers)
3. Main topics covered (maintenance, operations, spare parts, etc.)
4. Important procedures or specifications
5. Any critical safety or technical information

Document content:
{content_to_summarize}

Provide a clear, technical summary suitable for search and quick reference."""

        # Call API
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text

    except Exception as e:
        # Summarization is optional - continue without it
        logger.warning(f"Summarization failed for {document_id}: {e}")
        return ""
```

#### Step 4: Chunking

```python
def chunk_markdown(markdown_content: str) -> List[Dict[str, Any]]:
    """
    Chunk markdown by pages or sections

    Simple approach: chunk every 1000 characters
    Advanced: split by markdown headers or page markers
    """
    chunk_size = 1000
    chunks = []

    for i, start in enumerate(range(0, len(markdown_content), chunk_size), 1):
        content = markdown_content[start:start + chunk_size]
        chunks.append({
            "page": i,
            "content": content
        })

    return chunks
```

#### Step 5: Elasticsearch Indexing

```python
async def index_document(
    document_id: str,
    filename: str,
    chunks: List[Dict],
    summary: str,
    category: str,
    machine_model: Optional[str]
):
    """Index document pages in Elasticsearch"""

    try:
        # Update status
        await update_document_status(document_id, ProcessingStatus.INDEXING)

        # Index each chunk/page
        for chunk in chunks:
            es.index(
                index="documents",
                document={
                    "document_id": document_id,
                    "filename": filename,
                    "content": chunk["content"],
                    "page": chunk["page"],
                    "summary": summary,
                    "category": category,
                    "machine_model": machine_model,
                    "upload_date": datetime.utcnow().isoformat(),
                    "indexed_at": datetime.utcnow().isoformat(),
                    "processing_status": ProcessingStatus.READY.value
                }
            )

        # Refresh index
        es.indices.refresh(index="documents")

        # Update status to ready
        await update_document_status(document_id, ProcessingStatus.READY)

    except Exception as e:
        await update_document_status(
            document_id,
            ProcessingStatus.FAILED,
            error_message=str(e)
        )
        raise
```

### Error Handling

```python
async def process_document(document_id: str):
    """Main processing pipeline with error handling"""

    try:
        # Get document record
        doc = await get_document_record(document_id)

        # Step 1: Parse PDF
        markdown = await parse_pdf(document_id, doc.file_path)

        # Step 2: Generate summary (optional)
        try:
            summary = await generate_summary(document_id, markdown)
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            summary = ""

        # Step 3: Chunk content
        chunks = chunk_markdown(markdown)

        # Step 4: Index in Elasticsearch
        await index_document(
            document_id=document_id,
            filename=doc.filename,
            chunks=chunks,
            summary=summary,
            category=doc.category,
            machine_model=doc.machine_model
        )

        logger.info(f"Successfully processed document {document_id}")

    except Exception as e:
        logger.error(f"Processing failed for {document_id}: {e}")
        await update_document_status(
            document_id,
            ProcessingStatus.FAILED,
            error_message=str(e)
        )
```

---

## Search Implementation

### Elasticsearch Query Structure

```python
def build_search_query(
    query: str,
    category: Optional[List[str]] = None,
    machine_model: Optional[List[str]] = None,
    date_range: Optional[Dict] = None
) -> Dict:
    """Build Elasticsearch query with filters"""

    # Must clause - main search
    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": [
                    "content^2",      # Boost content field
                    "summary",
                    "filename"
                ],
                "fuzziness": "AUTO",  # Handle typos
                "operator": "or"
            }
        }
    ]

    # Filter clauses
    filter_clauses = []

    # Only search ready documents
    filter_clauses.append({
        "term": {"processing_status": "ready"}
    })

    if category:
        filter_clauses.append({
            "terms": {"category": category}
        })

    if machine_model:
        filter_clauses.append({
            "terms": {"machine_model": machine_model}
        })

    if date_range:
        date_filter = {"range": {"upload_date": {}}}
        if date_range.get("start"):
            date_filter["range"]["upload_date"]["gte"] = date_range["start"]
        if date_range.get("end"):
            date_filter["range"]["upload_date"]["lte"] = date_range["end"]
        filter_clauses.append(date_filter)

    return {
        "bool": {
            "must": must_clauses,
            "filter": filter_clauses
        }
    }
```

### Search Execution

```python
async def search_documents(
    query: str,
    filters: Optional[Dict] = None,
    size: int = 10,
    from_: int = 0
) -> SearchResponse:
    """Execute Elasticsearch search"""

    # Build query
    es_query = build_search_query(
        query=query,
        category=filters.get("category") if filters else None,
        machine_model=filters.get("machine_model") if filters else None,
        date_range=filters.get("date_range") if filters else None
    )

    # Execute search
    response = es.search(
        index="documents",
        query=es_query,
        size=size,
        from_=from_,
        highlight={
            "fields": {
                "content": {
                    "fragment_size": 200,
                    "number_of_fragments": 3,
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"]
                },
                "summary": {
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"]
                }
            }
        },
        aggs={
            "categories": {
                "terms": {"field": "category", "size": 10}
            },
            "machine_models": {
                "terms": {"field": "machine_model", "size": 20}
            }
        }
    )

    # Format results
    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "document_id": source["document_id"],
            "filename": source["filename"],
            "page": source["page"],
            "category": source.get("category"),
            "machine_model": source.get("machine_model"),
            "relevance_score": hit["_score"],
            "snippet": source["content"][:500],
            "summary": source.get("summary"),
            "highlights": hit.get("highlight", {}),
            "upload_date": source.get("upload_date")
        })

    return SearchResponse(
        results=results,
        total=response["hits"]["total"]["value"],
        query_time_ms=response["took"],
        facets=format_aggregations(response.get("aggregations", {}))
    )
```

### Fuzzy Matching Configuration

Elasticsearch's `fuzziness: "AUTO"` automatically handles:
- Typos (1-2 character edits based on term length)
  - Terms 1-2 chars: must match exactly
  - Terms 3-5 chars: 1 edit allowed
  - Terms 6+ chars: 2 edits allowed
- Transpositions (ab → ba)
- Missing characters (maintnance → maintenance)
- Extra characters (mainteenance → maintenance)

**Example:**
- Query: "maintainance" → Matches: "maintenance"
- Query: "convayor" → Matches: "conveyor"
- Query: "X200" → Matches: "X2000" (one edit)
- Query: "belt replcament" → Matches: "belt replacement"

### Advanced Query Optimization

**Boosting Strategy:**
```python
{
    "multi_match": {
        "query": query,
        "fields": [
            "content^2",          # Boost main content 2x
            "summary^1.5",        # Boost summary 1.5x
            "filename^1.2",       # Boost filename 1.2x
            "part_numbers^3",     # Boost part numbers 3x (most specific)
            "machine_model^2.5"   # Boost machine model 2.5x
        ],
        "type": "best_fields",    # Use highest scoring field
        "fuzziness": "AUTO",
        "operator": "or"          # Match any term (less strict)
    }
}
```

**Phrase Matching for Exact Terms:**
```python
{
    "bool": {
        "should": [
            {
                "multi_match": {  # Fuzzy keyword search
                    "query": query,
                    "fields": ["content", "summary"],
                    "fuzziness": "AUTO"
                }
            },
            {
                "match_phrase": {  # Exact phrase match (higher boost)
                    "content": {
                        "query": query,
                        "boost": 3
                    }
                }
            }
        ]
    }
}
```

**Custom Analyzers for Technical Terms:**
```python
# In index settings - for part numbers like "X2000-ABC-123"
{
    "analysis": {
        "analyzer": {
            "technical_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "asciifolding",  # Convert accented chars
                    "word_delimiter_graph"  # Split X2000-ABC → X2000, ABC
                ]
            }
        }
    }
}
```

---

## Infrastructure & Deployment

### MVP Architecture (Single Server)

```
┌────────────────────────────────────────┐
│         Single Server / VM             │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │     FastAPI Application          │ │
│  │     (Port 8000)                  │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │     Elasticsearch                │ │
│  │     (Port 9200)                  │ │
│  │     Single Node                  │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │     File Storage                 │ │
│  │     /data/pdfs/                  │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

### System Requirements

**Minimum (MVP):**
- **CPU:** 4 cores
- **RAM:** 16 GB (8GB for ES, 4GB for app, 4GB for OS)
- **Storage:** 500 GB SSD (for PDFs and ES indexes)
- **OS:** Ubuntu 22.04 LTS or similar

**Recommended (Production):**
- **CPU:** 8 cores
- **RAM:** 32 GB
- **Storage:** 1 TB SSD
- **Network:** 1 Gbps

### Elasticsearch Setup

**License:** Elasticsearch Basic (Free) - Includes all required features for our use case

```bash
# Install Elasticsearch 8.11+ (latest stable)
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.11.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.11.0-linux-x86_64.tar.gz
cd elasticsearch-8.11.0/

# Configure for single node (MVP)
cat > config/elasticsearch.yml <<EOF
# Cluster configuration
cluster.name: document-search
node.name: node-1

# Paths
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

# Network
network.host: localhost
http.port: 9200

# Discovery (single-node for MVP)
discovery.type: single-node

# Security (included in Basic tier)
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: false  # Enable for production

# Memory settings (adjust based on available RAM)
# Recommended: 50% of available RAM, max 32GB
# Set in jvm.options: -Xms8g -Xmx8g (for 16GB machine)
EOF

# Configure JVM heap size (edit config/jvm.options)
# For 16GB machine, allocate 8GB to Elasticsearch:
echo "-Xms8g" >> config/jvm.options
echo "-Xmx8g" >> config/jvm.options

# Start Elasticsearch
./bin/elasticsearch

# Save the generated elastic user password from first startup
# OR reset password with:
# ./bin/elasticsearch-reset-password -u elastic
```

**Important Notes:**
- **Free Tier:** All our required features (BM25, fuzzy matching, highlighting, aggregations, security) are included in the free Basic tier
- **No License Key Required:** Self-managed Elasticsearch Basic is completely free
- **Upgrade Path:** Can upgrade to Platinum ($125/month per node) or Enterprise ($175/month per node) for features like ELSER, Machine Learning, advanced security
- **Heap Size:** Elasticsearch recommends heap size = 50% of available RAM, max 32GB
- **Single Node → Cluster:** For production scaling, configure 3+ nodes with `discovery.seed_hosts`

### Application Deployment

```bash
# Clone repository
git clone <repo-url>
cd doc-parser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env <<EOF
# API Keys
VISION_AGENT_API_KEY=<landingai-key>
ANTHROPIC_API_KEY=<anthropic-key>

# Elasticsearch
ELASTICSEARCH_URL=https://localhost:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=<es-password>

# File Storage
PDF_STORAGE_PATH=/data/pdfs

# Application
API_KEY=<secure-api-key>
LOG_LEVEL=INFO
EOF

# Run application
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VISION_AGENT_API_KEY` | LandingAI API key | `aWJvM21yYTBpajFlbm...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-api03-...` |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint | `https://localhost:9200` |
| `ELASTICSEARCH_USER` | ES username | `elastic` |
| `ELASTICSEARCH_PASSWORD` | ES password | `<password>` |
| `PDF_STORAGE_PATH` | PDF file storage | `/data/pdfs` |
| `API_KEY` | API authentication key | `<secure-random-key>` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_FILE_SIZE_MB` | Max upload size | `100` |

### Cost Analysis

**Summary:** Very low operational costs with free Elasticsearch and pay-per-use APIs

#### Infrastructure Costs (Self-Managed)

| Component | Cost | Notes |
|-----------|------|-------|
| **Elasticsearch License** | **$0/month** | Basic tier is FREE for self-managed |
| **Server/VM (MVP)** | $50-100/month | 4-core, 16GB RAM, 500GB SSD (DigitalOcean/Hetzner/AWS) |
| **Server/VM (Production)** | $150-300/month | 8-core, 32GB RAM, 1TB SSD |
| **ES Cluster (3 nodes)** | $450-900/month | When scaling beyond single node |
| **S3 Storage (PDF files)** | $0.023/GB/month | ~$25/month for 1TB of PDFs |
| **Bandwidth** | Minimal | Internal use, low egress costs |

**Elasticsearch Upgrade Costs (if needed in future):**
- **Gold (discontinued for new):** N/A
- **Platinum:** $125/month per node (includes ELSER, ML, advanced security)
- **Enterprise:** $175/month per node (includes all features)

#### API Costs

**1. LandingAI ADE SDK (PDF Parsing)**
- Pricing: Contact LandingAI for custom pricing
- Estimated: $0.01-0.05 per page (rough estimate)
- **1,000 documents × 20 pages avg = 20,000 pages**
- **Estimated cost: $200-1,000 one-time** (depends on contract)

**2. Claude Haiku 3 (Summarization)**
- **Input:** $0.25 per million tokens
- **Output:** $1.25 per million tokens
- **Per document:** ~10K input tokens (first 100K chars), ~500 output tokens
- **Cost per document:** ~$0.0031 input + $0.00063 output = **$0.0037/doc**
- **1,000 documents:** ~$3.70
- **10,000 documents:** ~$37
- **Note:** Summaries cached in Elasticsearch (one-time cost per document)

#### Total Cost Estimates

**MVP (1,000 documents, 10-20 users):**
| Item | One-Time | Monthly |
|------|----------|---------|
| Server/VM | - | $75 |
| Elasticsearch | - | $0 (Basic tier) |
| PDF Parsing (LandingAI) | $200-1,000 | - |
| Summarization (Claude) | $4 | - |
| **Total** | **$204-1,004** | **$75/month** |

**Production (10,000 documents, 50 users):**
| Item | One-Time | Monthly |
|------|----------|---------|
| Server/VM | - | $200 |
| Elasticsearch | - | $0 (Basic tier) |
| PDF Parsing (LandingAI) | $2,000-10,000 | - |
| Summarization (Claude) | $37 | - |
| S3 Storage (optional) | - | $25 |
| **Total** | **$2,037-10,037** | **$225/month** |

**Cost Savings vs Time Savings:**
- **Time saved:** 30-60 min/search → 3 min = 27-57 min saved
- **Searches per month:** 100-500 searches/month (estimate)
- **Time saved:** 45-475 hours/month
- **Value (at $50/hour):** $2,250-23,750/month
- **ROI:** **10x-100x+ monthly operational costs**

### Monitoring & Logging

```python
# Logging configuration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Metrics to monitor
metrics = {
    "documents_uploaded": Counter(),
    "documents_processed": Counter(),
    "documents_failed": Counter(),
    "search_requests": Counter(),
    "search_latency": Histogram(),
    "api_errors": Counter()
}
```

**Key Metrics:**
- Documents uploaded/processed/failed (count)
- Search requests per minute
- Search latency (p50, p95, p99)
- API error rate
- Elasticsearch cluster health
- Disk usage

### Scaling Strategy

**Phase 1 (MVP): Single Node**
- 10,000 documents
- 10-20 concurrent users
- Single Elasticsearch node

**Phase 2 (Growth): Elasticsearch Cluster**
- 50,000 documents
- 50 concurrent users
- 3-node Elasticsearch cluster
- Load balancer for FastAPI app

**Phase 3 (Scale): Distributed**
- 100,000+ documents
- 100+ concurrent users
- 5+ node Elasticsearch cluster
- Multiple FastAPI app servers
- S3/Azure Blob for file storage
- Redis cache for summaries

---

## Security

### Authentication & Authorization

**MVP: API Key Authentication**
```python
async def verify_api_key(api_key: str = Header(...)):
    """Verify API key"""
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(401, "Invalid API key")
    return api_key
```

**Production: Consider**
- OAuth2 with JWT tokens
- Role-based access control (RBAC)
- User-level document permissions

### Input Validation

```python
from pydantic import BaseModel, validator

class DocumentUpload(BaseModel):
    category: str
    machine_model: Optional[str] = None

    @validator('category')
    def validate_category(cls, v):
        allowed = ['maintenance', 'operations', 'spare_parts']
        if v not in allowed:
            raise ValueError(f'Category must be one of {allowed}')
        return v
```

### Data Encryption

**At Rest:**
- **Elasticsearch:** Built-in encryption-at-rest (included in Basic tier with `xpack.security.enabled: true`)
- **File Storage:** Encrypted volumes (LUKS for Linux, BitLocker for Windows, or cloud provider encryption)
- **Database:** Use PostgreSQL with pgcrypto extension for sensitive fields

**In Transit:**
- **HTTPS/TLS 1.2+** for all API endpoints (required in production)
- **Elasticsearch TLS/SSL** enabled (`xpack.security.transport.ssl.enabled: true`)
- **Certificate Management:** Use Let's Encrypt or internal PKI for certificates

### Elasticsearch Security Features (Basic Tier - Free)

**Included in Free Self-Managed Basic:**
- ✅ **Authentication:** Basic auth, API keys, service tokens
- ✅ **Encrypted Communications:** TLS/SSL for transport and HTTP layers
- ✅ **Role-Based Access Control (RBAC):** Define roles with granular permissions
- ✅ **IP Filtering:** Restrict access by IP address
- ✅ **Anonymous Access Control:** Disable anonymous access

**Configuration Example:**
```yaml
# elasticsearch.yml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.keystore.path: certs/http.p12
xpack.security.transport.ssl.keystore.path: certs/transport.p12
```

**Create API Key for Application:**
```bash
# Create dedicated API key for application access
curl -X POST "localhost:9200/_security/api_key" \
  -H "Content-Type: application/json" \
  -u elastic:$ELASTIC_PASSWORD \
  -d '{
    "name": "doc-search-app",
    "role_descriptors": {
      "doc_search_role": {
        "cluster": ["monitor"],
        "indices": [
          {
            "names": ["documents", "summaries"],
            "privileges": ["read", "write", "create_index"]
          }
        ]
      }
    }
  }'
```

**Advanced Security (Requires Platinum+ License):**
- 🔒 Audit logging (track all access and changes)
- 🔒 Field/document level security (restrict access to specific fields/documents)
- 🔒 LDAP/Active Directory integration
- 🔒 SAML/Kerberos authentication
- 🔒 Space-level security (for Kibana)

**Note:** For MVP, Basic tier security is sufficient. Upgrade to Platinum ($125/month/node) if audit logging or advanced auth is required.

### Security Best Practices

1. **Never commit secrets** - Use `.env` files (git-ignored), consider HashiCorp Vault for production
2. **Validate all inputs** - Prevent injection attacks (use Pydantic models, sanitize user input)
3. **Rate limiting** - Prevent abuse (e.g., 100 requests/minute per IP using SlowAPI or Redis)
4. **CORS configuration** - Restrict allowed origins to frontend domain only
5. **API Key Rotation** - Rotate Elasticsearch API keys quarterly
6. **Audit logging** - Log all document uploads, deletions, and searches (app-level for MVP)
7. **Regular updates** - Keep dependencies patched (automate with Dependabot/Renovate)
8. **Least Privilege** - Use dedicated Elasticsearch roles with minimal required permissions
9. **Secure File Upload** - Validate file types, scan for malware, enforce size limits
10. **Session Management** - Use short-lived JWT tokens (15-30 min), refresh token rotation

---

## Performance

### Target Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Search latency | <3s (p95) | Elasticsearch `took` field |
| Document indexing | <5s per doc | Track processing time |
| API response time | <500ms | Application logs |
| Throughput | 50 concurrent users | Load testing |
| Document capacity | 10,000 (MVP) | Elasticsearch monitoring |

### Optimization Techniques

#### 1. Elasticsearch Optimization

```python
# Use bulk indexing for multiple documents
from elasticsearch.helpers import bulk

actions = [
    {
        "_index": "documents",
        "_source": {
            "document_id": doc_id,
            "content": content,
            ...
        }
    }
    for doc_id, content in documents
]

bulk(es, actions)
```

#### 2. Caching Strategy

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_summary(document_id: str) -> str:
    """Cache summaries in memory"""
    return get_summary_from_db(document_id)
```

**Cache summaries in Elasticsearch** to avoid re-generation.

#### 3. Async Processing

```python
# Use background tasks for document processing
@app.post("/api/v1/documents/upload")
async def upload(file: UploadFile, background_tasks: BackgroundTasks):
    document_id = create_document(file)
    background_tasks.add_task(process_document, document_id)
    return {"document_id": document_id, "status": "processing"}
```

#### 4. Connection Pooling

```python
# Reuse Elasticsearch connections
es = Elasticsearch(
    [ELASTICSEARCH_URL],
    basic_auth=(ES_USER, ES_PASSWORD),
    max_retries=3,
    retry_on_timeout=True,
    http_compress=True  # Enable compression
)
```

---

## Code Organization

### Project Structure

```
doc-parser/
├── .env                          # Environment variables (git-ignored)
├── .gitignore
├── README.md
├── requirements.txt              # Python dependencies
│
├── docs/                         # Documentation
│   ├── context_session.md
│   ├── technical_design_document.md
│   ├── elasticsearch_reference.md
│   └── api_documentation.md
│
├── tasks/                        # Planning documents
│   └── prd-document-search-system.md
│
├── src/                          # Application code
│   ├── __init__.py
│   │
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration management
│   │
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   ├── documents.py          # Document endpoints
│   │   └── search.py             # Search endpoints
│   │
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── document.py           # Document schemas
│   │   └── search.py             # Search schemas
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── document_processor.py # PDF processing pipeline
│   │   ├── pdf_parser.py         # LandingAI integration
│   │   ├── summarizer.py         # Claude integration
│   │   └── search_service.py     # Elasticsearch queries
│   │
│   ├── db/                       # Database/Elasticsearch
│   │   ├── __init__.py
│   │   ├── elasticsearch.py      # ES client setup
│   │   └── schema.py             # Index mappings
│   │
│   ├── storage/                  # File storage
│   │   ├── __init__.py
│   │   └── file_storage.py       # PDF storage logic
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── chunking.py           # Markdown chunking
│       ├── logging.py            # Logging setup
│       └── validators.py         # Input validation
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_api/
│   │   ├── test_documents.py
│   │   └── test_search.py
│   ├── test_services/
│   │   ├── test_pdf_parser.py
│   │   └── test_search_service.py
│   └── test_integration/
│       └── test_e2e_flow.py
│
└── data/                         # Local data (git-ignored)
    └── pdfs/                     # Uploaded PDF files
```

### Key Modules

#### `src/main.py` - FastAPI Application

```python
from fastapi import FastAPI
from src.api import documents, search
from src.db.elasticsearch import init_elasticsearch
from src.config import settings

app = FastAPI(
    title="Document Search API",
    version="1.0.0",
    description="Search and retrieval system for engineering documents"
)

# Include routers
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])

@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    await init_elasticsearch()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### `src/config.py` - Configuration

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Keys
    vision_agent_api_key: str
    anthropic_api_key: str

    # Elasticsearch
    elasticsearch_url: str = "https://localhost:9200"
    elasticsearch_user: str = "elastic"
    elasticsearch_password: str

    # Storage
    pdf_storage_path: str = "/data/pdfs"

    # Application
    api_key: str
    log_level: str = "INFO"
    max_file_size_mb: int = 100

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\       ← 10% (End-to-End)
       /──────\
      /Integration\  ← 30% (Integration)
     /────────────\
    /   Unit Tests  \ ← 60% (Unit)
   /────────────────\
```

### Unit Tests

```python
# tests/test_services/test_chunking.py
import pytest
from src.utils.chunking import chunk_markdown

def test_chunk_markdown_basic():
    """Test basic markdown chunking"""
    content = "A" * 2500  # 2500 characters
    chunks = chunk_markdown(content, chunk_size=1000)

    assert len(chunks) == 3
    assert chunks[0]["page"] == 1
    assert len(chunks[0]["content"]) == 1000

def test_chunk_markdown_empty():
    """Test chunking empty content"""
    chunks = chunk_markdown("")
    assert len(chunks) == 0
```

### Integration Tests

```python
# tests/test_integration/test_document_processing.py
import pytest
from src.services.document_processor import process_document

@pytest.mark.asyncio
async def test_full_document_processing(test_pdf):
    """Test complete document processing pipeline"""

    # Upload document
    doc_id = await upload_document(test_pdf)

    # Wait for processing
    await wait_for_processing(doc_id)

    # Verify indexed in Elasticsearch
    result = es.get(index="documents", id=doc_id)
    assert result["_source"]["processing_status"] == "ready"

    # Verify searchable
    search_result = await search_documents("test content")
    assert any(r["document_id"] == doc_id for r in search_result["results"])
```

### End-to-End Tests

```python
# tests/test_e2e/test_user_flow.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_complete_user_flow():
    """Test: Upload → Search → Retrieve"""

    # 1. Upload document
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        data={"category": "maintenance"},
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    assert response.status_code == 202
    doc_id = response.json()["document_id"]

    # 2. Wait for processing (poll status)
    wait_for_document_ready(doc_id)

    # 3. Search for document
    response = client.post(
        "/api/v1/search",
        json={"query": "test content"},
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0

    # 4. Retrieve document
    response = client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
```

### Performance Tests

```python
# tests/test_performance/test_search_latency.py
import pytest
import time

def test_search_response_time():
    """Test that search responds within 3 seconds"""

    queries = [
        "conveyor belt maintenance",
        "Model X2000 spare parts",
        "troubleshooting procedures"
    ]

    for query in queries:
        start = time.time()
        response = client.post("/api/v1/search", json={"query": query})
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 3.0, f"Search took {elapsed}s (target: <3s)"
```

---

## Development Phases

### Phase 1A: Core MVP (Weeks 1-4)

**Goal:** Basic document upload, indexing, and search

#### Week 1: Infrastructure Setup
- [ ] Set up Elasticsearch (single node)
- [ ] Create FastAPI project structure
- [ ] Configure environment variables
- [ ] Implement health check endpoint
- [ ] Set up logging

#### Week 2: Document Upload & Processing
- [ ] Implement PDF upload endpoint
- [ ] Integrate LandingAI parser
- [ ] Implement markdown chunking
- [ ] Index documents in Elasticsearch
- [ ] Unit tests for processing pipeline

#### Week 3: Search Implementation
- [ ] Implement search endpoint
- [ ] Build Elasticsearch queries (BM25)
- [ ] Add highlighting and snippets
- [ ] Implement pagination
- [ ] Unit tests for search

#### Week 4: Testing & Refinement
- [ ] Integration tests
- [ ] E2E tests
- [ ] Performance testing with sample documents
- [ ] Bug fixes and optimization

**Deliverables:**
- Working API for upload and search
- 10-20 test documents indexed
- Basic documentation

---

### Phase 1B: Enhanced Features (Weeks 5-8)

**Goal:** Add summarization, filtering, admin features

#### Week 5: Summarization
- [ ] Integrate Claude Haiku 3
- [ ] Implement summarization in pipeline
- [ ] Test summary quality with sales team
- [ ] Add summary to search results

#### Week 6: Filters & Advanced Search
- [ ] Implement category filters
- [ ] Implement machine_model filters
- [ ] Implement date range filters
- [ ] Add fuzzy matching tuning
- [ ] Add aggregations (facets)

#### Week 7: Admin Features
- [ ] Implement document list endpoint
- [ ] Implement document delete endpoint
- [ ] Add document download endpoint
- [ ] Build simple admin UI (optional)

#### Week 8: Pilot Deployment
- [ ] Deploy to test environment
- [ ] Index 100-500 real documents
- [ ] Pilot with 5 sales agents
- [ ] Collect feedback and iterate

**Deliverables:**
- Full-featured API
- 100-500 documents indexed
- Pilot user feedback
- Performance metrics

---

## Risks & Mitigations

### Technical Risks

#### 1. PDF Parsing Quality
**Risk:** LandingAI may fail on poor-quality or scanned PDFs
**Impact:** High - affects all downstream processing
**Mitigation:**
- Validate parser with diverse document samples
- Implement quality checks after parsing
- Gracefully handle parsing failures (flag for manual review)
- Consider fallback parser (PyMuPDF) for simple PDFs

#### 2. Search Quality
**Risk:** BM25 may not handle complex semantic queries well
**Impact:** Medium - affects user experience
**Mitigation:**
- Collect user feedback on search quality
- Optimize analyzers and fuzzy matching
- Plan for ELSER semantic search in Phase 2 if needed
- Test with real user queries during pilot

#### 3. Elasticsearch Performance
**Risk:** Single node may not handle load or large document sets
**Impact:** Medium - affects scalability
**Mitigation:**
- Start with 10K document target
- Monitor performance metrics
- Plan for cluster scaling if needed
- Optimize queries and index settings

#### 4. API Cost (Claude Haiku 3)
**Risk:** Summarization costs may be higher than expected
**Impact:** Low-Medium - affects operational costs
**Mitigation:**
- Summarization is optional for MVP
- Cache summaries to avoid re-generation
- Monitor API usage and costs
- Can disable summarization if budget exceeded

### Operational Risks

#### 5. User Adoption
**Risk:** Users may not adopt new tool or prefer old methods
**Impact:** High - affects ROI
**Mitigation:**
- Pilot with early adopters
- Training and onboarding sessions
- Demonstrate time savings with metrics
- Collect feedback and iterate quickly

#### 6. Data Quality
**Risk:** Poor quality source documents affect system value
**Impact:** Medium
**Mitigation:**
- Document review before upload
- Clean up and organize existing documentation
- Implement document versioning
- Archive outdated documents

---

## Future Enhancements

### Phase 2: Advanced Search (Q2 2025)

**ELSER Semantic Search** (Requires Elasticsearch Platinum License - $125/month/node):
```python
# Add ELSER sparse vectors to index
{
    "ml.inference.elser_embeddings": {
        "type": "sparse_vector"
    }
}

# Hybrid search query (combines BM25 + ELSER)
{
    "bool": {
        "should": [
            {
                "multi_match": {  # BM25 keyword search (free)
                    "query": query,
                    "fields": ["content", "summary"]
                }
            },
            {
                "text_expansion": {  # ELSER semantic search (Platinum+)
                    "ml.inference.elser_embeddings": {
                        "model_id": ".elser_model_2",
                        "model_text": query
                    }
                }
            }
        ]
    }
}
```

**Benefits:**
- Better natural language query handling
- Understands synonyms and concepts
- Hybrid approach combines exact + semantic matching

### Phase 3: Multi-Format Support (Q3 2025)

**Word Document Support:**
- Use `python-docx` for DOCX parsing
- Extract text and preserve structure
- Handle embedded images and tables

**Excel Spreadsheet Support:**
- Use `openpyxl` or `pandas` for XLSX parsing
- Extract cell values and formulas
- Convert tables to markdown format

### Phase 4: Advanced Features (Q4 2025)

- **Automated request understanding** from emails/tickets
- **Response generation** using RAG (Retrieval-Augmented Generation)
- **Advanced analytics** (search trends, popular documents)
- **Document comparison** (diff between versions)
- **Multi-language support** (translate queries and documents)

---

## Conclusion

This Technical Design Document provides a comprehensive blueprint for implementing the document search and retrieval system. The design prioritizes:

1. **Pragmatism:** Leverages existing proven code patterns
2. **Simplicity:** Focuses on MVP scope with clear scaling path
3. **Quality:** Targets 90% time reduction with validated technologies
4. **Flexibility:** Easy to upgrade (Haiku 3 → 3.5, single node → cluster, BM25 → hybrid)

**Key Success Factors:**
- Reuse existing Elasticsearch implementation patterns
- Leverage validated LandingAI parser
- Start simple (single node, basic search)
- Iterate based on user feedback
- Scale incrementally as needed

**Next Steps:**
1. Review and approve this TDD
2. Set up development environment
3. Begin Phase 1A implementation
4. Pilot with real users and iterate

---

**Document Version History:**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-02 | Initial TDD | Tech Lead |
| 1.1 | 2025-10-02 | Updated with Elasticsearch best practices: licensing (Basic tier free), security features (API keys, RBAC, TLS), cost analysis ($0 ES license), enhanced search implementation (fuzzy matching, boosting, custom analyzers), infrastructure setup guide, ELSER upgrade path (Platinum+ required) | Tech Lead |

**References:**
- [Product Requirements Document](../tasks/prd-document-search-system.md)
- [Context Session](./context_session.md)
- [Elasticsearch Reference](./elasticsearch_reference.md)
- [Project Overview](../CLAUDE.md)

---

**Document End**
