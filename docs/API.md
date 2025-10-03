# API Documentation

**Version**: 1.0.0
**Base URL**: `http://localhost:8000`
**Last Updated**: October 3, 2025

## Overview

The Document Search & Retrieval System provides a RESTful API for:
- **Document Management**: Upload, retrieve, list, delete, and download PDF documents
- **Search**: Full-text search with fuzzy matching, filters, and highlighting
- **Health Monitoring**: System health checks

All document management endpoints require API key authentication via the `Authorization` header.

## Authentication

### API Key Authentication

All document management endpoints require an API key passed in the `Authorization` header:

```http
Authorization: Bearer your_api_key_here
```

To configure your API key, set it in the `.env` file:

```bash
API_KEY=your_secure_api_key_here
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid or missing API key"
}
```

## Endpoints

### Table of Contents

**Health & Status**
- [GET /health](#get-health) - Health check endpoint

**Document Management** (requires authentication)
- [POST /api/v1/documents/upload](#post-apiv1documentsupload) - Upload a PDF document
- [GET /api/v1/documents/{document_id}](#get-apiv1documentsdocument_id) - Get document status
- [GET /api/v1/documents](#get-apiv1documents) - List documents with filters
- [DELETE /api/v1/documents/{document_id}](#delete-apiv1documentsdocument_id) - Delete a document
- [GET /api/v1/documents/{document_id}/download](#get-apiv1documentsdocument_iddownload) - Download PDF

**Search** (public)
- [POST /api/v1/search](#post-apiv1search) - Search documents

---

## Health & Status

### GET /health

Health check endpoint to verify service availability.

**Authentication**: None required

#### Request

```http
GET /health HTTP/1.1
Host: localhost:8000
```

#### Response

**Status**: `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Document Search & Retrieval System"
}
```

#### Example

```bash
curl http://localhost:8000/health
```

---

## Document Management

### POST /api/v1/documents/upload

Upload a PDF document for processing. The document will be parsed, chunked, summarized, and indexed for search.

**Authentication**: Required (API key)

#### Request

**Content-Type**: `multipart/form-data`

**Form Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF file to upload (max 100MB) |
| `category` | String | Yes | Document category: `maintenance`, `operations`, or `spare_parts` |
| `machine_model` | String | No | Machine model identifier (e.g., "AGV-2000") |

#### Response

**Status**: `202 Accepted`

```json
{
  "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
  "filename": "maintenance_manual.pdf",
  "status": "uploaded",
  "upload_date": "2025-10-03T10:30:00.000Z"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | String (UUID) | Unique identifier for the document |
| `filename` | String | Original filename |
| `status` | String | Processing status (always "uploaded" initially) |
| `upload_date` | String (ISO 8601) | Upload timestamp |

#### Processing Status Flow

1. `uploaded` - Document received, queued for processing
2. `parsing` - Extracting text and tables from PDF
3. `ready` - Processing complete, document searchable
4. `failed` - Processing failed (check `error_message`)

#### Error Responses

**400 Bad Request** - Invalid file or parameters:
```json
{
  "detail": "Only PDF files are allowed"
}
```

**400 Bad Request** - Invalid category:
```json
{
  "detail": "Invalid category. Must be one of: ['maintenance', 'operations', 'spare_parts']"
}
```

**413 Request Entity Too Large** - File too large:
```json
{
  "detail": "File size exceeds maximum allowed size of 100MB"
}
```

**401 Unauthorized** - Missing/invalid API key:
```json
{
  "detail": "Invalid or missing API key"
}
```

#### Example

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer your_api_key_here" \
  -F "file=@/path/to/maintenance_manual.pdf" \
  -F "category=maintenance" \
  -F "machine_model=AGV-2000"
```

#### Notes

- **Background Processing**: Document processing happens asynchronously. Use the [GET /api/v1/documents/{document_id}](#get-apiv1documentsdocument_id) endpoint to check status.
- **Page Limit**: PDFs with >50 pages are automatically truncated to 50 pages (LandingAI limitation). A note will appear in `error_message`.
- **Processing Time**: Approximately 10-15 seconds per page.

---

### GET /api/v1/documents/{document_id}

Retrieve document metadata and processing status.

**Authentication**: Required (API key)

#### Request

```http
GET /api/v1/documents/{document_id} HTTP/1.1
Host: localhost:8000
Authorization: Bearer your_api_key_here
```

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | String (UUID) | Document identifier from upload response |

#### Response

**Status**: `200 OK`

```json
{
  "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
  "filename": "maintenance_manual.pdf",
  "status": "ready",
  "upload_date": "2025-10-03T10:30:00.000Z",
  "indexed_at": "2025-10-03T10:31:15.000Z",
  "total_pages": 42,
  "error_message": null
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | String (UUID) | Unique identifier |
| `filename` | String | Original filename |
| `status` | String | Processing status: `uploaded`, `parsing`, `ready`, `failed` |
| `upload_date` | String (ISO 8601) | Upload timestamp |
| `indexed_at` | String (ISO 8601) or `null` | When indexing completed |
| `total_pages` | Integer or `null` | Number of pages in PDF |
| `error_message` | String or `null` | Error details if status is `failed`, or truncation notice |

**Truncation Notice Example**:
```json
{
  "status": "ready",
  "total_pages": 50,
  "error_message": "Note: Original PDF had 164 pages, processed first 50 pages only"
}
```

#### Error Responses

**404 Not Found** - Document doesn't exist:
```json
{
  "detail": "Document not found: e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e"
}
```

**401 Unauthorized**:
```json
{
  "detail": "Invalid or missing API key"
}
```

#### Example

```bash
curl -X GET "http://localhost:8000/api/v1/documents/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e" \
  -H "Authorization: Bearer your_api_key_here"
```

---

### GET /api/v1/documents

List documents with optional filters and pagination.

**Authentication**: Required (API key)

#### Request

```http
GET /api/v1/documents?status=ready&category=maintenance&page=1&page_size=10 HTTP/1.1
Host: localhost:8000
Authorization: Bearer your_api_key_here
```

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | String | No | All | Filter by status: `uploaded`, `parsing`, `ready`, `failed` |
| `category` | String | No | All | Filter by category: `maintenance`, `operations`, `spare_parts` |
| `page` | Integer | No | 1 | Page number (1-indexed) |
| `page_size` | Integer | No | 10 | Items per page (max 100) |

#### Response

**Status**: `200 OK`

```json
{
  "total": 45,
  "page": 1,
  "page_size": 10,
  "documents": [
    {
      "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
      "filename": "maintenance_manual.pdf",
      "file_size": 8912345,
      "file_path": "/data/pdfs/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e.pdf",
      "category": "maintenance",
      "machine_model": "AGV-2000",
      "part_numbers": [],
      "upload_date": "2025-10-03T10:30:00.000Z",
      "processing_status": "ready",
      "indexed_at": "2025-10-03T10:31:15.000Z",
      "error_message": null,
      "total_pages": 42
    }
  ]
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `total` | Integer | Total number of documents matching filters |
| `page` | Integer | Current page number |
| `page_size` | Integer | Number of items per page |
| `documents` | Array | Array of document metadata objects |

**Document Object Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | String (UUID) | Unique identifier |
| `filename` | String | Original filename |
| `file_size` | Integer | File size in bytes |
| `file_path` | String | Server-side storage path |
| `category` | String | Document category |
| `machine_model` | String or `null` | Machine model identifier |
| `part_numbers` | Array | Extracted part numbers (currently empty) |
| `upload_date` | String (ISO 8601) | Upload timestamp |
| `processing_status` | String | Processing status |
| `indexed_at` | String (ISO 8601) or `null` | Indexing completion time |
| `error_message` | String or `null` | Error details or truncation notice |
| `total_pages` | Integer or `null` | Number of pages |

#### Error Responses

**400 Bad Request** - Invalid pagination:
```json
{
  "detail": "Page must be >= 1"
}
```

**400 Bad Request** - Invalid status:
```json
{
  "detail": "Invalid status. Must be one of: ['uploaded', 'parsing', 'ready', 'failed']"
}
```

**401 Unauthorized**:
```json
{
  "detail": "Invalid or missing API key"
}
```

#### Example

```bash
# List all ready maintenance documents
curl -X GET "http://localhost:8000/api/v1/documents?status=ready&category=maintenance&page=1&page_size=10" \
  -H "Authorization: Bearer your_api_key_here"

# List all documents (no filters)
curl -X GET "http://localhost:8000/api/v1/documents?page=1&page_size=20" \
  -H "Authorization: Bearer your_api_key_here"
```

---

### DELETE /api/v1/documents/{document_id}

Delete a document and all associated data (PDF file, database record, Elasticsearch index entries).

**Authentication**: Required (API key)

#### Request

```http
DELETE /api/v1/documents/{document_id} HTTP/1.1
Host: localhost:8000
Authorization: Bearer your_api_key_here
```

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | String (UUID) | Document identifier |

#### Response

**Status**: `204 No Content`

No response body on success.

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Document not found: e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e"
}
```

**401 Unauthorized**:
```json
{
  "detail": "Invalid or missing API key"
}
```

#### Example

```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e" \
  -H "Authorization: Bearer your_api_key_here"
```

#### Notes

- **Permanent**: This operation is irreversible. The PDF file, database record, and all indexed pages are deleted.
- **Graceful Degradation**: If Elasticsearch or file deletion fails, the database record is still deleted.

---

### GET /api/v1/documents/{document_id}/download

Download the original PDF document.

**Authentication**: Required (API key)

#### Request

```http
GET /api/v1/documents/{document_id}/download HTTP/1.1
Host: localhost:8000
Authorization: Bearer your_api_key_here
```

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | String (UUID) | Document identifier |

#### Response

**Status**: `200 OK`
**Content-Type**: `application/pdf`
**Content-Disposition**: `attachment; filename="maintenance_manual.pdf"`

Binary PDF file content.

#### Error Responses

**404 Not Found** - Document doesn't exist:
```json
{
  "detail": "Document not found: e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e"
}
```

**404 Not Found** - PDF file missing:
```json
{
  "detail": "PDF file not found for document e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e"
}
```

**401 Unauthorized**:
```json
{
  "detail": "Invalid or missing API key"
}
```

#### Example

```bash
# Download and save to file
curl -X GET "http://localhost:8000/api/v1/documents/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e/download" \
  -H "Authorization: Bearer your_api_key_here" \
  --output maintenance_manual.pdf

# Display download progress
curl -X GET "http://localhost:8000/api/v1/documents/e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e/download" \
  -H "Authorization: Bearer your_api_key_here" \
  --output manual.pdf \
  --progress-bar
```

---

## Search

### POST /api/v1/search

Search documents with full-text search, fuzzy matching, filters, and highlighting.

**Authentication**: None required (public endpoint)

#### Request

**Content-Type**: `application/json`

```json
{
  "query": "motor replacement procedure",
  "enable_fuzzy": true,
  "include_highlights": true,
  "include_content": false,
  "page": 1,
  "page_size": 10,
  "filters": {
    "category": "maintenance",
    "machine_model": "AGV-2000",
    "date_from": "2025-01-01",
    "date_to": "2025-12-31"
  }
}
```

**Request Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | String | Yes | - | Search query text |
| `enable_fuzzy` | Boolean | No | `false` | Enable fuzzy matching for typos (1-2 char edits) |
| `include_highlights` | Boolean | No | `true` | Include highlighted snippets in results |
| `include_content` | Boolean | No | `false` | Include full page content (HTML with tables) |
| `page` | Integer | No | 1 | Page number (1-indexed) |
| `page_size` | Integer | No | 10 | Results per page (max 100) |
| `filters` | Object | No | `{}` | Optional filters |

**Filter Fields** (all optional):

| Field | Type | Description |
|-------|------|-------------|
| `category` | String | Filter by category: `maintenance`, `operations`, `spare_parts` |
| `machine_model` | String | Filter by machine model (exact match) |
| `date_from` | String (ISO date) | Filter documents uploaded on/after this date |
| `date_to` | String (ISO date) | Filter documents uploaded on/before this date |

#### Response

**Status**: `200 OK`

```json
{
  "results": [
    {
      "document_id": "e2f8350e-01a1-4f6d-9eb9-3ce96bc7936e",
      "filename": "maintenance_manual.pdf",
      "page_number": 15,
      "content_snippet": "To perform <em>motor replacement</em>, first disconnect power from the main circuit breaker. Remove the four M8 bolts securing the <em>motor</em> housing...",
      "summary": "This section covers motor replacement procedures including safety precautions, required tools, and step-by-step instructions.",
      "score": 12.453,
      "category": "maintenance",
      "machine_model": "AGV-2000",
      "upload_date": "2025-10-03T10:30:00.000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "took_ms": 55
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `results` | Array | Array of search result objects |
| `total` | Integer | Total number of matching results |
| `page` | Integer | Current page number |
| `page_size` | Integer | Results per page |
| `took_ms` | Integer | Search execution time in milliseconds |

**Search Result Object Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | String (UUID) | Document identifier |
| `filename` | String | Original filename |
| `page_number` | Integer | Page number where match was found |
| `content_snippet` | String | Highlighted snippet (~150 chars) with `<em>` tags around matches |
| `summary` | String | AI-generated page summary |
| `full_content` | String | Full page content (only if `include_content: true`) |
| `score` | Float | BM25 relevance score (higher = better match) |
| `category` | String | Document category |
| `machine_model` | String or `null` | Machine model identifier |
| `upload_date` | String (ISO 8601) | Upload timestamp |

#### Error Responses

**400 Bad Request** - Missing query:
```json
{
  "detail": "Query parameter is required"
}
```

**400 Bad Request** - Invalid pagination:
```json
{
  "detail": "Page size must be between 1 and 100"
}
```

**400 Bad Request** - Invalid filter:
```json
{
  "detail": "Invalid category. Must be one of: ['maintenance', 'operations', 'spare_parts']"
}
```

#### Examples

**Basic Search**:
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "motor replacement",
    "page": 1,
    "page_size": 10
  }'
```

**Fuzzy Search with Filters**:
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "moter replacment",
    "enable_fuzzy": true,
    "include_highlights": true,
    "filters": {
      "category": "maintenance",
      "machine_model": "AGV-2000"
    }
  }'
```

**Search with Full Content**:
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "spare parts list",
    "include_content": true,
    "filters": {
      "category": "spare_parts"
    }
  }'
```

#### Search Algorithm Details

**Field Boosting**:
- `part_numbers`: 3.0x (highest priority)
- `machine_model`: 2.5x
- `content`: 2.0x
- `summary`: 1.5x

**Fuzzy Matching** (`enable_fuzzy: true`):
- AUTO mode: 1 character edit for terms 3-5 chars, 2 edits for 6+ chars
- Handles typos like "moter" → "motor", "replacment" → "replacement"

**Highlighting**:
- `<em>` tags around matched terms
- Snippet length: ~150 characters centered on best match
- Multiple matches highlighted in single snippet

---

## Data Models

### DocumentCategory

Enum of valid document categories:

- `maintenance` - Maintenance manuals
- `operations` - Operation instructions
- `spare_parts` - Spare parts catalogs

### ProcessingStatus

Enum of document processing statuses:

- `uploaded` - Document received, queued for processing
- `parsing` - Extracting text and tables from PDF
- `ready` - Processing complete, document searchable
- `failed` - Processing failed (check `error_message`)

---

## Rate Limits

**Current Limits**:
- No rate limits on search endpoint (public)
- No rate limits on document management endpoints (authenticated)

**External API Limits**:
- LandingAI: Subject to API rate limits (429 errors possible)
- Claude API: Subject to API rate limits

**Recommendations**:
- Upload documents sequentially to avoid LandingAI rate limits
- Wait 1-2 seconds between uploads for best results

---

## Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200 OK` | Request successful |
| `202 Accepted` | Document upload accepted, processing queued |
| `204 No Content` | Delete successful |
| `400 Bad Request` | Invalid request parameters or validation error |
| `401 Unauthorized` | Missing or invalid API key |
| `404 Not Found` | Document or resource not found |
| `413 Request Entity Too Large` | File size exceeds 100MB limit |
| `500 Internal Server Error` | Server error (check logs) |

### Common Error Response Format

```json
{
  "detail": "Error message here"
}
```

---

## Interactive Documentation

For interactive API exploration:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both interfaces allow you to:
- Try API endpoints directly in the browser
- View request/response schemas
- See example requests and responses
- Test authentication

---

## SDK Examples

### Python

```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000"

# Upload document
with open("manual.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": f},
        data={
            "category": "maintenance",
            "machine_model": "AGV-2000"
        }
    )
    document_id = response.json()["document_id"]

# Check status
response = requests.get(
    f"{BASE_URL}/api/v1/documents/{document_id}",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
print(response.json()["status"])

# Search
response = requests.post(
    f"{BASE_URL}/api/v1/search",
    json={
        "query": "motor replacement",
        "enable_fuzzy": True,
        "filters": {"category": "maintenance"}
    }
)
results = response.json()["results"]
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000';

// Upload document
async function uploadDocument() {
  const form = new FormData();
  form.append('file', fs.createReadStream('manual.pdf'));
  form.append('category', 'maintenance');
  form.append('machine_model', 'AGV-2000');

  const response = await axios.post(
    `${BASE_URL}/api/v1/documents/upload`,
    form,
    {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        ...form.getHeaders()
      }
    }
  );
  return response.data.document_id;
}

// Search
async function search(query) {
  const response = await axios.post(
    `${BASE_URL}/api/v1/search`,
    {
      query: query,
      enable_fuzzy: true,
      filters: { category: 'maintenance' }
    }
  );
  return response.data.results;
}
```

### cURL

See examples in each endpoint section above.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-03 | Initial release with full CRUD and search functionality |

---

**For Issues**: Please report bugs or request features via GitHub issues.
**Support**: See [README.md](../README.md) for troubleshooting and setup help.
