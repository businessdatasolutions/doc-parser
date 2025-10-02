"""
Document summarization service using Claude Haiku 3.
"""

from typing import Optional
from anthropic import Anthropic

from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class Summarizer:
    """Document summarizer using Claude Haiku 3."""

    def __init__(self):
        """Initialize Anthropic client."""
        self._client: Optional[Anthropic] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Create Anthropic client with API key."""
        try:
            self._client = Anthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

    @property
    def client(self) -> Anthropic:
        """Get the Anthropic client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client

    def summarize_text(
        self,
        content: str,
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 500
    ) -> str:
        """
        Summarize text content using Claude Haiku 3.

        Args:
            content: Text content to summarize
            model: Claude model to use
            max_tokens: Maximum tokens in summary

        Returns:
            str: Summary of the content

        Raises:
            ValueError: If content is empty or too short
            Exception: For API errors
        """
        if not content or len(content.strip()) < 50:
            raise ValueError("Content is too short to summarize")

        # Truncate content if too long (Claude context limit)
        # Haiku 3 has 200K context, but we'll limit input for cost
        max_input_chars = 100000  # ~25K tokens
        if len(content) > max_input_chars:
            logger.warning(
                f"Content truncated from {len(content)} to {max_input_chars} chars"
            )
            content = content[:max_input_chars]

        logger.info(f"Summarizing {len(content)} characters with {model}")

        try:
            # Create summary prompt optimized for technical documents
            system_prompt = (
                "You are a technical documentation summarizer for industrial equipment. "
                "Create concise summaries that capture:\n"
                "1. Main topics and key information\n"
                "2. Important part numbers, model numbers, or specifications\n"
                "3. Critical procedures or warnings\n"
                "Keep the summary factual and technical."
            )

            user_prompt = (
                f"Summarize the following technical document page in 2-4 concise sentences. "
                f"Focus on the main topics, key specifications, and important details:\n\n"
                f"{content}"
            )

            # Call Claude API
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract summary from response
            summary = message.content[0].text.strip()

            logger.info(
                f"Generated summary: {len(summary)} chars "
                f"(input tokens: {message.usage.input_tokens}, "
                f"output tokens: {message.usage.output_tokens})"
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            raise

    def summarize_text_with_retry(
        self,
        content: str,
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 500,
        max_retries: int = 3
    ) -> str:
        """
        Summarize text with retry logic for transient failures.

        Args:
            content: Text content to summarize
            model: Claude model to use
            max_tokens: Maximum tokens in summary
            max_retries: Maximum number of retry attempts

        Returns:
            str: Summary of the content

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Summarization attempt {attempt}/{max_retries}")
                return self.summarize_text(content, model=model, max_tokens=max_tokens)

            except Exception as e:
                last_error = e
                logger.warning(f"Summarization attempt {attempt}/{max_retries} failed: {e}")

                if attempt == max_retries:
                    logger.error(f"All {max_retries} summarization attempts failed")
                    raise last_error

                # Wait before retry (exponential backoff)
                import time
                time.sleep(2 ** attempt)

        # Should never reach here, but for type safety
        raise last_error

    def batch_summarize(
        self,
        contents: list[str],
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 500
    ) -> list[str]:
        """
        Summarize multiple text contents.

        Args:
            contents: List of text contents to summarize
            model: Claude model to use
            max_tokens: Maximum tokens per summary

        Returns:
            list: List of summaries

        Note: This processes sequentially, not in parallel, to respect API rate limits.
        """
        summaries = []

        for i, content in enumerate(contents, 1):
            logger.info(f"Summarizing content {i}/{len(contents)}")

            try:
                summary = self.summarize_text_with_retry(
                    content,
                    model=model,
                    max_tokens=max_tokens
                )
                summaries.append(summary)

            except Exception as e:
                logger.error(f"Failed to summarize content {i}: {e}")
                # Add empty summary on failure
                summaries.append("")

        return summaries


# Global summarizer instance
_summarizer: Optional[Summarizer] = None


def get_summarizer() -> Summarizer:
    """
    Get the global summarizer instance (singleton pattern).

    Returns:
        Summarizer: The summarizer instance
    """
    global _summarizer
    if _summarizer is None:
        _summarizer = Summarizer()
    return _summarizer
