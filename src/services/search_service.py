"""
Search service for querying documents in Elasticsearch.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from src.db.elasticsearch import get_elasticsearch_client
from src.models.search import SearchRequest, SearchResponse, SearchResult, SearchFilters
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for searching documents using Elasticsearch."""

    def __init__(self):
        """Initialize search service with Elasticsearch client."""
        self.es_client = get_elasticsearch_client()
        self.index_name = "documents"

    def search(self, request: SearchRequest) -> SearchResponse:
        """
        Execute search query with filters and return results.

        Args:
            request: Search request with query and parameters

        Returns:
            SearchResponse: Search results with metadata

        Raises:
            Exception: If search fails
        """
        logger.info(
            f"Executing search: query='{request.query}', "
            f"page={request.page}, size={request.page_size}"
        )

        # Build Elasticsearch query
        es_query = self._build_query(request)

        # Calculate pagination
        from_offset = (request.page - 1) * request.page_size

        # Execute search
        try:
            es_response = self.es_client.client.search(
                index=self.index_name,
                body=es_query,
                size=request.page_size,
                from_=from_offset
            )

            # Parse results
            response = self._parse_response(
                es_response=es_response,
                query=request.query,
                page=request.page,
                page_size=request.page_size,
                include_highlights=request.include_highlights,
                include_content=request.include_content
            )

            logger.info(
                f"Search completed: {response.total} results in {response.took}ms"
            )

            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _build_query(self, request: SearchRequest) -> Dict[str, Any]:
        """
        Build Elasticsearch query from search request.

        Args:
            request: Search request parameters

        Returns:
            dict: Elasticsearch query DSL
        """
        # Build multi-match query with field boosting
        query_clause = {
            "multi_match": {
                "query": request.query,
                "fields": [
                    "part_numbers^3",      # Highest priority
                    "machine_model^2.5",   # Machine model
                    "content^2",           # Main content
                    "summary^1.5",         # Summary
                    "filename^1.2"         # Filename
                ],
                "type": "best_fields",
                "operator": "or"
            }
        }

        # Add fuzzy matching if enabled
        if request.enable_fuzzy:
            query_clause["multi_match"]["fuzziness"] = "AUTO"

        # Build bool query with filters
        bool_query = {
            "must": [query_clause]
        }

        # Add filters
        if request.filters:
            filter_clauses = self._build_filters(request.filters)
            if filter_clauses:
                bool_query["filter"] = filter_clauses

        # Complete query structure
        es_query = {
            "query": {
                "bool": bool_query
            },
            "sort": [
                "_score",  # Sort by relevance score
                {"upload_date": {"order": "desc"}}  # Then by upload date
            ]
        }

        # Add highlighting if requested
        if request.include_highlights:
            highlight_fields = {
                "summary": {
                    "fragment_size": 150,
                    "number_of_fragments": 1,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            }

            # Add content highlighting
            if request.include_content:
                # Full-field highlighting for full content view
                highlight_fields["content"] = {
                    "number_of_fragments": 0,  # Return entire field highlighted
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            else:
                # Fragment highlighting for snippet view
                highlight_fields["content"] = {
                    "fragment_size": 150,
                    "number_of_fragments": 1,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }

            es_query["highlight"] = {
                "fields": highlight_fields,
                "order": "score"
            }

        return es_query

    def _build_filters(self, filters: SearchFilters) -> List[Dict[str, Any]]:
        """
        Build Elasticsearch filter clauses from search filters.

        Args:
            filters: Search filters

        Returns:
            list: List of filter clauses
        """
        filter_clauses = []

        # Category filter
        if filters.category:
            filter_clauses.append({
                "term": {"category": filters.category.value}
            })

        # Machine model filter
        if filters.machine_model:
            filter_clauses.append({
                "term": {"machine_model": filters.machine_model}
            })

        # Date range filter
        if filters.date_from or filters.date_to:
            date_range = {}
            if filters.date_from:
                date_range["gte"] = filters.date_from.isoformat()
            if filters.date_to:
                date_range["lte"] = filters.date_to.isoformat()

            filter_clauses.append({
                "range": {"upload_date": date_range}
            })

        # Part numbers filter
        if filters.part_numbers:
            filter_clauses.append({
                "terms": {"part_numbers": filters.part_numbers}
            })

        return filter_clauses

    def _parse_response(
        self,
        es_response: Dict[str, Any],
        query: str,
        page: int,
        page_size: int,
        include_highlights: bool,
        include_content: bool = True
    ) -> SearchResponse:
        """
        Parse Elasticsearch response into SearchResponse model.

        Args:
            es_response: Raw Elasticsearch response
            query: Original search query
            page: Current page number
            page_size: Results per page
            include_highlights: Whether to include highlighted snippets
            include_content: Whether to include full page content

        Returns:
            SearchResponse: Parsed search response
        """
        total = es_response["hits"]["total"]["value"]
        took = es_response["took"]

        results = []
        for hit in es_response["hits"]["hits"]:
            source = hit["_source"]
            score = hit["_score"]

            # Extract highlight snippet and full highlighted content
            snippet = None
            highlighted_content = None

            if include_highlights and "highlight" in hit:
                # Extract highlighted content (full-field when include_content=True)
                if "content" in hit["highlight"] and include_content:
                    # Full-field highlighting - use for highlighted_content
                    highlighted_content = hit["highlight"]["content"][0]

                # Extract snippet for preview (prefer summary, fall back to content fragment)
                if "summary" in hit["highlight"]:
                    snippet = hit["highlight"]["summary"][0]
                elif "content" in hit["highlight"] and not include_content:
                    # Content fragment (when include_content=False) - use for snippet
                    snippet = hit["highlight"]["content"][0]

            # Create search result
            result = SearchResult(
                document_id=source["document_id"],
                filename=source["filename"],
                page=source["page"],
                category=source["category"],
                score=score,
                snippet=snippet,
                content=source.get("content") if include_content else None,
                highlighted_content=highlighted_content,
                summary=source.get("summary"),
                machine_model=source.get("machine_model"),
                part_numbers=source.get("part_numbers", []),
                upload_date=source.get("upload_date")
            )
            results.append(result)

        return SearchResponse(
            query=query,
            total=total,
            page=page,
            page_size=page_size,
            took=took,
            results=results
        )


# Global search service instance
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """
    Get the global search service instance (singleton pattern).

    Returns:
        SearchService: The search service instance
    """
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
