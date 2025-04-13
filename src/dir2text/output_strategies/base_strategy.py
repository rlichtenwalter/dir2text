"""Output strategy base class defining the interface for file content formatting.

This module provides the abstract base class that defines how file content should be
formatted for output. It establishes the contract that concrete strategies must follow
for handling file content formatting, including requirements for token count placement.
"""

from abc import ABC, abstractmethod
from typing import Optional


class OutputStrategy(ABC):
    """Abstract base class defining the interface for file content output formatting strategies.

    This class implements the Strategy pattern for formatting file content output in different
    formats (e.g., XML, JSON). Each concrete strategy implements methods to wrap file content
    with appropriate formatting, including optional metadata like token counts.

    The output process is divided into three phases:
    1. Start - outputs opening format wrapper with file metadata
    2. Content - formats the actual file content
    3. End - outputs closing format wrapper with optional metadata

    Token count handling varies by format. Some formats (like XML) require token counts
    in the opening wrapper, while others (like JSON) can handle them in either opening
    or closing wrappers. Concrete implementations must specify their requirements via
    the requires_tokens_in_start property.

    Example:
        >>> class CustomStrategy(OutputStrategy):
        ...     @property
        ...     def requires_tokens_in_start(self) -> bool:
        ...         return True  # Tokens must be in opening wrapper
        ...
        ...     def format_start(self, path: str, token_count: Optional[int] = None) -> str:
        ...         count_str = f' tokens="{token_count}"' if token_count is not None else ''
        ...         return f"<file path='{path}'{count_str}>\\n"
        ...
        ...     def format_content(self, content: str) -> str:
        ...         return content
        ...
        ...     def format_end(self, token_count: Optional[int] = None) -> str:
        ...         if token_count is not None:
        ...             raise ValueError("Token count not allowed in format_end")
        ...         return "</file>\\n"
        ...
        ...     def get_file_extension(self) -> str:
        ...         return ".custom"
    """

    @property
    @abstractmethod
    def requires_tokens_in_start(self) -> bool:
        """Indicates whether token counts must be provided in format_start.

        Returns:
            bool: True if token counts must be provided in format_start (and not in format_end),
                False if token counts can be provided in format_end.

        Note:
            When this property returns True:
            - Token counts must be provided in format_start if available
            - Token counts must not be provided in format_end
            - format_end should raise ValueError if token_count is provided

            When this property returns False:
            - Token counts should be consistent between format_start and format_end
            - Both methods should handle None gracefully
        """
        pass

    @abstractmethod
    def format_start(self, relative_path: str, file_token_count: Optional[int] = None) -> str:
        """Format the opening wrapper for a file's content.

        This method is called once at the start of each file's content to output any
        necessary opening format markers and metadata.

        Args:
            relative_path: The relative path of the file being formatted.
            file_token_count: Total token count for the file's content if token
                counting is enabled. Must be provided if requires_tokens_in_start
                is True and token counting is enabled.

        Returns:
            The formatted opening wrapper string.

        Raises:
            ValueError: If requires_tokens_in_start is True and file_token_count
                is required but not provided.
        """
        pass

    @abstractmethod
    def format_content(self, content: str) -> str:
        """Format a chunk of file content.

        This method is called one or more times with chunks of the file's content.
        The content should be appropriately escaped/formatted for the output format
        but should not include format-specific wrappers.

        Args:
            content: A chunk of file content to format.

        Returns:
            The formatted content string.
        """
        pass

    @abstractmethod
    def format_end(self, file_token_count: Optional[int] = None) -> str:
        """Format the closing wrapper for a file's content.

        This method is called once at the end of each file's content to output any
        necessary closing format markers and final metadata.

        Args:
            file_token_count: Total token count for the file's content if token
                counting is enabled. Must not be provided if requires_tokens_in_start
                is True.

        Returns:
            The formatted closing wrapper string.

        Raises:
            ValueError: If requires_tokens_in_start is True and file_token_count
                is provided, or if requires_tokens_in_start is False and the count
                doesn't match what was provided to format_start.
        """
        pass

    @abstractmethod
    def format_symlink(self, relative_path: str, target_path: str) -> str:
        """Format a symbolic link entry.

        This method is called to format symlink information for output.
        Unlike files, symlinks don't have content chunks, so only a single
        method is needed.

        Args:
            relative_path: The relative path of the symlink.
            target_path: The target path that the symlink points to.

        Returns:
            The formatted symlink string.
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the appropriate file extension for this output format.

        Returns:
            The file extension including the leading dot (e.g., ".xml", ".json").
        """
        pass
