# Elasticsearch Implementation Reference

**Purpose:** This document provides reference patterns and code examples from existing Elasticsearch implementation that can be reused for the document search system.

**Date:** October 2, 2025

---

## Overview

This project will use Elasticsearch for full-text search (BM25 algorithm) instead of vector embeddings. This decision is based on:

1. **Existing proven patterns** - Reuse working Elasticsearch code
2. **Simpler infrastructure** - No GPU requirements
3. **Excellent for technical documents** - Strong at exact matching (part numbers, model names)
4. **Cost-effective** - No API fees, no embedding costs
5. **Extensible** - Can add ELSER semantic search later if needed

---

## Existing Elasticsearch Implementation

The following code patterns from the existing Elasticsearch implementation can be reused and adapted:

### 1. Elasticsearch Client Setup

```python
from elasticsearch import Elasticsearch

# Initialize Elasticsearch client
es = Elasticsearch(
    ["https://localhost:9200"],
    basic_auth=("elastic", "password"),
    verify_certs=False,
    ssl_show_warn=False
)
```

**Adaptation needed:**
- Use environment variables for credentials
- Configure for production (enable certificate verification)
- Support multiple Elasticsearch nodes

---

### 2. Index Creation with Mappings

```python
def create_index(index_name: str):
    """Create an index with basic text analysis settings"""
    if es.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists, skipping creation")
        return

    es.indices.create(
        index=index_name,
        settings={
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "default": {
                        "type": "standard"
                    }
                }
            }
        },
        mappings={
            "properties": {
                "content": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "page": {
                    "type": "integer"
                }
            }
        }
    )
```

**Adaptation for document search system:**

```python
def create_documents_index():
    """Create index for engineering documents with metadata"""
    if es.indices.exists(index="documents"):
        return

    es.indices.create(
        index="documents",
        settings={
            "number_of_shards": 1,
            "number_of_replicas": 1,  # Add replica for production
            "analysis": {
                "analyzer": {
                    "default": {
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
        mappings={
            "properties": {
                "document_id": {"type": "keyword"},
                "filename": {"type": "keyword"},
                "content": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "summary": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "page": {"type": "integer"},
                "category": {
                    "type": "keyword"  # For filtering: maintenance, operations, spare_parts
                },
                "machine_model": {
                    "type": "keyword",  # For filtering
                    "analyzer": "part_number_analyzer"
                },
                "upload_date": {"type": "date"},
                "file_size": {"type": "long"}
            }
        }
    )
```

**Key improvements:**
- Added metadata fields (document_id, filename, category, machine_model)
- Custom analyzer for part numbers (case-insensitive exact matching)
- Summary field for quick document overview
- Replica for production reliability

---

### 3. Document Indexing

```python
def index_document(index_name: str, content: str, page: int):
    """Index a document page"""
    es.index(
        index=index_name,
        document={
            "content": content,
            "page": page
        }
    )
```

**Adaptation for document search system:**

```python
from uuid import uuid4
from datetime import datetime

def index_document_page(
    document_id: str,
    filename: str,
    content: str,
    page: int,
    category: str = None,
    machine_model: str = None,
    summary: str = None
):
    """Index a single page of a document with metadata"""
    es.index(
        index="documents",
        document={
            "document_id": document_id,
            "filename": filename,
            "content": content,
            "summary": summary,
            "page": page,
            "category": category,
            "machine_model": machine_model,
            "upload_date": datetime.utcnow().isoformat(),
        }
    )

def index_full_document(
    filename: str,
    pages_content: List[Dict[str, str]],  # [{"page": 1, "content": "..."}]
    category: str = None,
    machine_model: str = None,
    summary: str = None
):
    """Index all pages of a document"""
    document_id = str(uuid4())

    for page_data in pages_content:
        index_document_page(
            document_id=document_id,
            filename=filename,
            content=page_data["content"],
            page=page_data["page"],
            category=category,
            machine_model=machine_model,
            summary=summary
        )

    # Refresh index to make documents searchable immediately
    es.indices.refresh(index="documents")

    return document_id
```

**Key improvements:**
- Page-level indexing for precise results
- Document ID groups pages from same document
- Metadata attached to each page
- Returns document_id for reference

---

### 4. Search Implementation

```python
def search_elasticsearch(index_name: str, query: str, size: int = 5) -> List[Dict]:
    """Perform a basic search"""
    response = es.search(
        index=index_name,
        query={
            "match": {
                "content": query
            }
        },
        size=size,
        highlight={
            "fields": {
                "content": {}
            }
        }
    )

    results = []
    for hit in response['hits']['hits']:
        results.append({
            'score': hit['_score'],
            'page': hit['_source']['page'],
            'content_snippet': hit['_source']['content'][:500],
            'highlights': hit.get('highlight', {}).get('content', [])
        })

    return results
```

**Adaptation for document search system:**

```python
def search_documents(
    query: str,
    category: str = None,
    machine_model: str = None,
    date_from: str = None,
    date_to: str = None,
    size: int = 10
) -> List[Dict]:
    """
    Search documents with optional filters

    Args:
        query: Search query string
        category: Filter by category (maintenance, operations, spare_parts)
        machine_model: Filter by machine model
        date_from: Filter by upload date (ISO format)
        date_to: Filter by upload date (ISO format)
        size: Number of results to return

    Returns:
        List of search results with highlights
    """

    # Build query
    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": ["content^2", "summary", "filename"],  # Boost content field
                "fuzziness": "AUTO"  # Handle typos
            }
        }
    ]

    # Build filters
    filter_clauses = []
    if category:
        filter_clauses.append({"term": {"category": category}})
    if machine_model:
        filter_clauses.append({"term": {"machine_model": machine_model}})
    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        filter_clauses.append({"range": {"upload_date": date_range}})

    # Execute search
    response = es.search(
        index="documents",
        query={
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        },
        size=size,
        highlight={
            "fields": {
                "content": {
                    "fragment_size": 200,
                    "number_of_fragments": 3
                },
                "summary": {}
            }
        },
        # Return aggregations for faceted search (optional)
        aggs={
            "categories": {
                "terms": {"field": "category"}
            },
            "machine_models": {
                "terms": {"field": "machine_model"}
            }
        }
    )

    results = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        results.append({
            'document_id': source['document_id'],
            'filename': source['filename'],
            'page': source['page'],
            'category': source.get('category'),
            'machine_model': source.get('machine_model'),
            'score': hit['_score'],
            'content_snippet': source['content'][:500],
            'summary': source.get('summary'),
            'highlights': hit.get('highlight', {}),
            'upload_date': source.get('upload_date')
        })

    return {
        'results': results,
        'total': response['hits']['total']['value'],
        'aggregations': response.get('aggregations', {})
    }
```

**Key improvements:**
- Multi-field search (content, summary, filename)
- Fuzzy matching for typo tolerance
- Filtering by metadata (category, machine_model, date)
- Highlighting with configurable fragment size
- Aggregations for faceted search (show available filters)
- Returns document ID to group pages from same document

---

### 5. Results Formatting

```python
def format_search_results(document_name: str, results: List[Dict]) -> str:
    """Format search results as readable text"""
    if not results:
        return f"No results found in {document_name}"

    output = f"Results from {document_name}:\n\n"

    for i, result in enumerate(results, 1):
        output += f"Result {i}:\n"
        output += f"  Relevance Score: {result['score']:.2f}\n"
        output += f"  Page: {result['page']}\n"

        if result['highlights']:
            output += f"  Highlighted Text:\n"
            for highlight in result['highlights']:
                output += f"    {highlight}\n"
        else:
            output += f"  Content Preview:\n"
            output += f"    {result['content_snippet']}\n"

        output += "\n"

    return output
```

**Adaptation for API response:**

```python
def format_api_response(search_results: Dict) -> Dict:
    """Format search results for API response"""
    return {
        "results": [
            {
                "document_id": result['document_id'],
                "filename": result['filename'],
                "page": result['page'],
                "category": result.get('category'),
                "machine_model": result.get('machine_model'),
                "relevance_score": round(result['score'], 2),
                "snippet": result['content_snippet'],
                "summary": result.get('summary'),
                "highlights": result.get('highlights', {}),
                "upload_date": result.get('upload_date')
            }
            for result in search_results['results']
        ],
        "total_results": search_results['total'],
        "facets": {
            "categories": [
                {"name": bucket['key'], "count": bucket['doc_count']}
                for bucket in search_results.get('aggregations', {}).get('categories', {}).get('buckets', [])
            ],
            "machine_models": [
                {"name": bucket['key'], "count": bucket['doc_count']}
                for bucket in search_results.get('aggregations', {}).get('machine_models', {}).get('buckets', [])
            ]
        }
    }
```

---

## Integration with LandingAI Parser

### PDF Processing and Indexing Pipeline

```python
from landingai_ade import LandingAIADE
from pathlib import Path
import os

def process_and_index_pdf(
    pdf_path: str,
    category: str = None,
    machine_model: str = None
) -> str:
    """
    Parse PDF with LandingAI and index in Elasticsearch

    Returns:
        document_id: UUID of indexed document
    """
    # 1. Parse PDF with LandingAI
    api_key = os.getenv("VISION_AGENT_API_KEY")
    client = LandingAIADE(apikey=api_key)

    parse_response = client.parse(
        document=Path(pdf_path),
        model="dpt-2-latest",
    )

    if not parse_response.markdown:
        raise ValueError("PDF parsing failed - no markdown output")

    # 2. Extract markdown content (already validated to work well)
    markdown_content = parse_response.markdown

    # 3. Optional: Generate summary using Claude Haiku 3.5
    summary = generate_summary_with_claude_haiku(markdown_content)

    # 4. Split markdown by sections or pages (simple approach: split by page markers)
    pages_content = split_markdown_by_pages(markdown_content)

    # 5. Index in Elasticsearch
    filename = Path(pdf_path).name
    document_id = index_full_document(
        filename=filename,
        pages_content=pages_content,
        category=category,
        machine_model=machine_model,
        summary=summary
    )

    return document_id

def split_markdown_by_pages(markdown: str) -> List[Dict[str, str]]:
    """
    Split markdown content by pages
    Simple approach: split by anchor tags or every N tokens
    """
    # TODO: Implement smart splitting
    # For now, simple approach: chunk every 1000 characters
    chunk_size = 1000
    pages = []
    for i, start in enumerate(range(0, len(markdown), chunk_size), 1):
        content = markdown[start:start + chunk_size]
        pages.append({"page": i, "content": content})
    return pages

def generate_summary_with_claude_haiku(markdown_content: str) -> str:
    """
    Generate document summary using Claude Haiku 3

    Uses Claude Haiku 3 for development/testing phase.
    Can easily upgrade to Claude Haiku 3.5 by changing model parameter.

    Args:
        markdown_content: Full markdown content of the document

    Returns:
        150-300 word summary
    """
    import anthropic
    import os

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Truncate content if too long (keep first 100K characters)
    content_to_summarize = markdown_content[:100000]

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

    message = client.messages.create(
        model="claude-3-haiku-20240307",  # Claude Haiku 3 for development/testing
        # For production upgrade: use "claude-3-5-haiku-20241022" if quality improvement needed
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text
```

---

## Document Management Operations

### Delete Document

```python
def delete_document(document_id: str):
    """Delete all pages of a document by document_id"""
    es.delete_by_query(
        index="documents",
        query={
            "term": {"document_id": document_id}
        }
    )
    es.indices.refresh(index="documents")
```

### Update Document

```python
def update_document(document_id: str, new_pdf_path: str, category: str = None, machine_model: str = None):
    """Update a document by deleting old version and re-indexing"""
    # Delete old version
    delete_document(document_id)

    # Re-index new version
    return process_and_index_pdf(new_pdf_path, category, machine_model)
```

### List Documents

```python
def list_documents(page: int = 1, limit: int = 50, category: str = None) -> Dict:
    """List all documents (grouped by document_id)"""

    # Build filter
    filters = []
    if category:
        filters.append({"term": {"category": category}})

    # Aggregate by document_id to get unique documents
    response = es.search(
        index="documents",
        query={"bool": {"filter": filters}} if filters else {"match_all": {}},
        size=0,  # No individual results
        aggs={
            "unique_documents": {
                "terms": {
                    "field": "document_id",
                    "size": limit,
                    "order": {"latest_upload": "desc"}
                },
                "aggs": {
                    "latest_upload": {"max": {"field": "upload_date"}},
                    "filename": {"terms": {"field": "filename", "size": 1}},
                    "category": {"terms": {"field": "category", "size": 1}},
                    "page_count": {"value_count": {"field": "page"}}
                }
            }
        }
    )

    documents = []
    for bucket in response['aggregations']['unique_documents']['buckets']:
        documents.append({
            "document_id": bucket['key'],
            "filename": bucket['filename']['buckets'][0]['key'] if bucket['filename']['buckets'] else None,
            "category": bucket['category']['buckets'][0]['key'] if bucket['category']['buckets'] else None,
            "upload_date": bucket['latest_upload']['value_as_string'],
            "page_count": bucket['page_count']['value']
        })

    return {
        "documents": documents,
        "total": len(documents),
        "page": page
    }
```

---

## Testing Strategy

### Sample Search Queries for Testing

```python
# Test exact matching (part numbers, model names)
test_queries = [
    "X2000",  # Model name
    "conveyor belt",  # Common term
    "Model X2000 conveyor belt replacement",  # Combined
    "maintainance procedure",  # Typo - should fuzzy match "maintenance"
    "How do I replace the belt?",  # Natural language
]

for query in test_queries:
    results = search_documents(query, size=5)
    print(f"\nQuery: {query}")
    print(f"Results: {results['total']}")
    for result in results['results'][:3]:
        print(f"  - {result['filename']} (page {result['page']}, score {result['score']:.2f})")
```

---

## Performance Considerations

### Indexing Performance
- Index pages in batches using `bulk` API
- Use `refresh=False` during bulk indexing, then refresh once at the end
- Monitor index size and shard health

### Search Performance
- Use filters (`filter` clause) instead of queries for exact matches
- Filter clauses are cached by Elasticsearch
- Limit `size` to 10-20 results for UI
- Use pagination for large result sets

---

## Future Enhancements

### 1. Add ELSER Semantic Search (Hybrid)

```python
# When ready to add semantic capabilities
def hybrid_search(query: str, size: int = 10):
    """Combine BM25 and ELSER semantic search"""
    return es.search(
        index="documents",
        query={
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["content", "summary"]
                        }
                    },
                    {
                        "text_expansion": {
                            "ml.inference.elser_embeddings": {
                                "model_id": ".elser_model_2",
                                "model_text": query
                            }
                        }
                    }
                ]
            }
        },
        size=size
    )
```

### 2. Custom Analyzers for Technical Terms

```python
# Add domain-specific analyzers
"analysis": {
    "analyzer": {
        "technical_term_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "asciifolding", "technical_synonyms"]
        }
    },
    "filter": {
        "technical_synonyms": {
            "type": "synonym",
            "synonyms": [
                "repair, fix, maintenance",
                "replace, substitute, swap",
                "belt, conveyor belt",
            ]
        }
    }
}
```

---

## Summary

This reference document provides:

1. ✅ **Proven patterns** from existing Elasticsearch implementation
2. ✅ **Adaptations** for the document search system
3. ✅ **Integration** with LandingAI PDF parser
4. ✅ **Document management** operations
5. ✅ **Testing strategy** and sample queries
6. ✅ **Future enhancements** roadmap

**Next steps:**
1. Set up Elasticsearch cluster (single node for MVP)
2. Implement adapted indexing and search functions
3. Integrate with LandingAI parser
4. Build REST API endpoints
5. Test with sample documents
6. Iterate based on search quality feedback

---

**Document End**
