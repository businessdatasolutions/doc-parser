"""
Search request and response models.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

from src.models.document import DocumentCategory


class SearchFilters(BaseModel):
    """Search filters for narrowing results."""

    category: Optional[DocumentCategory] = Field(
        default=None,
        description="Filter by document category"
    )
    machine_model: Optional[str] = Field(
        default=None,
        description="Filter by machine model"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter documents uploaded after this date"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter documents uploaded before this date"
    )
    part_numbers: Optional[List[str]] = Field(
        default=None,
        description="Filter by part numbers"
    )

    @validator("date_to")
    def validate_date_range(cls, v, values):
        """Ensure date_to is after date_from."""
        if v and "date_from" in values and values["date_from"]:
            if v < values["date_from"]:
                raise ValueError("date_to must be after date_from")
        return v


class SearchRequest(BaseModel):
    """Search request parameters."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query text"
    )
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional filters to narrow results"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination"
    )
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results per page"
    )
    enable_fuzzy: bool = Field(
        default=True,
        description="Enable fuzzy matching (AUTO fuzziness)"
    )
    include_highlights: bool = Field(
        default=True,
        description="Include highlighted snippets in results"
    )
    include_content: bool = Field(
        default=True,
        description="Include full page content with preserved structure (tables, formatting)"
    )

    @validator("query")
    def validate_query(cls, v):
        """Validate and clean query string."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty or whitespace")
        return v


class SearchResult(BaseModel):
    """Individual search result."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original PDF filename")
    page: int = Field(..., description="Page number within document")
    category: str = Field(..., description="Document category")
    score: float = Field(..., description="Relevance score from Elasticsearch")

    snippet: Optional[str] = Field(
        default=None,
        description="Highlighted text snippet showing matched content"
    )
    content: Optional[str] = Field(
        default=None,
        description="Full page content with preserved structure (tables, formatting)"
    )
    highlighted_content: Optional[str] = Field(
        default=None,
        description="Full page content with search terms highlighted using <mark> tags"
    )
    summary: Optional[str] = Field(
        default=None,
        description="AI-generated summary of the page"
    )
    machine_model: Optional[str] = Field(
        default=None,
        description="Machine model if specified"
    )
    part_numbers: Optional[List[str]] = Field(
        default_factory=list,
        description="Part numbers found on this page"
    )
    upload_date: Optional[datetime] = Field(
        default=None,
        description="Date document was uploaded"
    )


class SearchResponse(BaseModel):
    """Search response with results and metadata."""

    query: str = Field(..., description="Original search query")
    total: int = Field(..., description="Total number of matching results")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    took: int = Field(..., description="Search time in milliseconds")

    results: List[SearchResult] = Field(
        default_factory=list,
        description="List of search results"
    )

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages."""
        return self.page > 1
