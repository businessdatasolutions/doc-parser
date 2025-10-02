"""
Search API endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from src.models.search import SearchRequest, SearchResponse, SearchFilters
from src.services.search_service import get_search_service
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Search"])


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """
    Search for documents using natural language query.

    This endpoint provides full-text search across all indexed documents with:
    - Multi-field search with relevance boosting
    - Fuzzy matching for typo tolerance
    - Filtering by category, machine model, date range, and part numbers
    - Highlighted snippets showing matched content
    - Pagination support

    **Field Boosting:**
    - Part numbers: 3x
    - Machine model: 2.5x
    - Content: 2x
    - Summary: 1.5x
    - Filename: 1.2x

    **Example queries:**
    - "cartoner machine specifications"
    - "part number 12345"
    - "installation procedure"
    - "safety requirements"

    Args:
        request: Search request with query and optional filters

    Returns:
        SearchResponse: Search results with metadata

    Raises:
        HTTPException: 400 if query is invalid, 500 if search fails
    """
    try:
        logger.info(f"Search request: query='{request.query}', page={request.page}")

        # Execute search
        search_service = get_search_service()
        response = search_service.search(request)

        logger.info(
            f"Search completed: {response.total} results, "
            f"{response.took}ms, page {response.page}/{response.total_pages}"
        )

        return response

    except ValueError as e:
        logger.warning(f"Invalid search request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed. Please try again later."
        )
