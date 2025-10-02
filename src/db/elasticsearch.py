"""
Elasticsearch client and index management for Document Search & Retrieval System.
"""

from typing import Optional, Dict, Any
from elasticsearch import Elasticsearch, exceptions
from elasticsearch.helpers import bulk

from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ElasticsearchClient:
    """Elasticsearch client with connection pooling and error handling."""

    def __init__(self):
        """Initialize Elasticsearch client."""
        self._client: Optional[Elasticsearch] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Create Elasticsearch client with configuration."""
        try:
            # Build authentication if credentials provided
            basic_auth = None
            if settings.elasticsearch_user and settings.elasticsearch_password:
                basic_auth = (
                    settings.elasticsearch_user,
                    settings.elasticsearch_password
                )

            self._client = Elasticsearch(
                [settings.elasticsearch_url],
                basic_auth=basic_auth,
                max_retries=3,
                retry_on_timeout=True,
                http_compress=True,
                request_timeout=30,
            )

            logger.info(
                f"Elasticsearch client initialized: {settings.elasticsearch_url}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")
            raise

    @property
    def client(self) -> Elasticsearch:
        """Get the Elasticsearch client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client

    def health_check(self) -> Dict[str, Any]:
        """
        Check Elasticsearch cluster health.

        Returns:
            dict: Cluster health information

        Raises:
            ConnectionError: If Elasticsearch is not reachable
        """
        try:
            health = self.client.cluster.health()
            logger.info(
                f"Elasticsearch health check: status={health['status']}, "
                f"nodes={health['number_of_nodes']}"
            )
            return health
        except exceptions.ConnectionError as e:
            logger.error(f"Elasticsearch connection failed: {e}")
            raise ConnectionError(
                f"Failed to connect to Elasticsearch at {settings.elasticsearch_url}"
            ) from e
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            raise

    def ping(self) -> bool:
        """
        Ping Elasticsearch to check if it's reachable.

        Returns:
            bool: True if Elasticsearch is reachable, False otherwise
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Elasticsearch ping failed: {e}")
            return False

    def create_index(
        self,
        index_name: str,
        mappings: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create an Elasticsearch index with mappings and settings.

        Args:
            index_name: Name of the index to create
            mappings: Index mappings configuration
            settings: Optional index settings

        Returns:
            bool: True if index was created, False if it already exists

        Raises:
            Exception: If index creation fails
        """
        try:
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index '{index_name}' already exists")
                return False

            body = {"mappings": mappings}
            if settings:
                body["settings"] = settings

            self.client.indices.create(index=index_name, body=body)
            logger.info(f"Created index '{index_name}'")
            return True

        except exceptions.RequestError as e:
            logger.error(f"Failed to create index '{index_name}': {e.info}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating index '{index_name}': {e}")
            raise

    def delete_index(self, index_name: str) -> bool:
        """
        Delete an Elasticsearch index.

        Args:
            index_name: Name of the index to delete

        Returns:
            bool: True if index was deleted, False if it didn't exist
        """
        try:
            if not self.client.indices.exists(index=index_name):
                logger.warning(f"Index '{index_name}' does not exist")
                return False

            self.client.indices.delete(index=index_name)
            logger.info(f"Deleted index '{index_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete index '{index_name}': {e}")
            raise

    def index_document(
        self,
        index_name: str,
        document: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> str:
        """
        Index a single document.

        Args:
            index_name: Name of the index
            document: Document to index
            doc_id: Optional document ID

        Returns:
            str: Document ID
        """
        try:
            response = self.client.index(
                index=index_name,
                document=document,
                id=doc_id
            )
            return response['_id']

        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            raise

    def bulk_index(
        self,
        index_name: str,
        documents: list[Dict[str, Any]]
    ) -> tuple[int, list]:
        """
        Bulk index multiple documents.

        Args:
            index_name: Name of the index
            documents: List of documents to index

        Returns:
            tuple: (success_count, errors)
        """
        try:
            actions = [
                {
                    "_index": index_name,
                    "_source": doc
                }
                for doc in documents
            ]

            success, errors = bulk(
                self.client,
                actions,
                raise_on_error=False,
                stats_only=False
            )

            logger.info(
                f"Bulk indexed {success} documents to '{index_name}', "
                f"{len(errors)} errors"
            )

            return success, errors

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            raise

    def search(
        self,
        index_name: str,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """
        Search documents in an index.

        Args:
            index_name: Name of the index to search
            query: Elasticsearch query DSL
            size: Number of results to return
            from_: Starting offset for pagination

        Returns:
            dict: Search results
        """
        try:
            response = self.client.search(
                index=index_name,
                body=query,
                size=size,
                from_=from_
            )
            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def close(self) -> None:
        """Close the Elasticsearch client connection."""
        if self._client:
            self._client.close()
            logger.info("Elasticsearch client connection closed")


# Global Elasticsearch client instance
_es_client: Optional[ElasticsearchClient] = None


def get_elasticsearch_client() -> ElasticsearchClient:
    """
    Get the global Elasticsearch client instance (singleton pattern).

    Returns:
        ElasticsearchClient: The Elasticsearch client
    """
    global _es_client
    if _es_client is None:
        _es_client = ElasticsearchClient()
    return _es_client
