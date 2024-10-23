"""JSON output strategy for file content formatting.

This module provides a strategy for formatting file content as JSON objects,
supporting flexible token count placement and proper JSON escaping.
"""

import json
from typing import Optional

from .base_strategy import OutputStrategy


class JSONOutputStrategy(OutputStrategy):
    """Output strategy that formats file content as JSON objects.

    This strategy formats each file's content as a JSON object with the following structure:
    {
        "path": "relative/path/to/file",
        "content": "file content...",
        "tokens": 123  # Optional, only included if token counting is enabled
    }

    The strategy handles streaming content in chunks while maintaining valid JSON structure
    and proper escaping. Each file's content is formatted as a single JSON string value,
    with appropriate escaping of special characters.

    Token counts can be provided in either format_start or format_end, but must be
    consistent if provided in both. This flexibility allows for both streaming and
    post-processed token counting approaches.

    Attributes:
        encoder: JSON encoder instance used for consistent escaping.
        token_count: Token count provided at format_start, used for consistency
            validation at format_end.

    Example:
        >>> strategy = JSONOutputStrategy()
        >>> print(strategy.format_start("example.py", 42))
        {"path": "example.py", "content": "
        >>> print(strategy.format_content('print("Hello")\\n'))
        print(\\"Hello\\")\\n
        >>> print(strategy.format_end(42))
        ", "tokens": 42}
    """

    def __init__(self) -> None:
        """Initialize the JSON output strategy.

        Creates a JSON encoder instance for consistent escaping and initializes the
        token count tracking.
        """
        self.encoder = json.JSONEncoder()
        self.token_count: Optional[int] = None

    @property
    def requires_tokens_in_start(self) -> bool:
        """Indicates whether token counts must be provided in format_start.

        JSON format is flexible about token count placement, allowing counts in
        either the opening or closing portion of the output.

        Returns:
            bool: False, indicating token counts can be provided in format_end.
        """
        return False

    def format_start(self, relative_path: str, file_token_count: Optional[int] = None) -> str:
        """Format the start of a JSON object for a file.

        Creates the opening portion of a JSON object including the path and starting
        the content field. The object is intentionally left unclosed to allow for
        streaming content.

        Args:
            relative_path: The relative path of the file being formatted.
            file_token_count: Total token count for the file. If provided, will be
                validated against any token count provided in format_end.

        Returns:
            The opening portion of the JSON object, ending with an opening quote
            for the content string.

        Example:
            >>> strategy = JSONOutputStrategy()
            >>> print(strategy.format_start("src/main.py", 150))
            {"path": "src/main.py", "content": "
        """
        data = {"path": relative_path}
        self.token_count = file_token_count

        # Start the JSON object and the content field
        start = self.encoder.encode(data)
        start = start.rstrip("}")  # Remove the closing brace
        start += ', "content": "'

        return start

    def format_content(self, content: str) -> str:
        """Format a chunk of file content for JSON inclusion.

        Escapes the content chunk for inclusion in a JSON string value. The content
        is escaped without surrounding quotes since it's part of a larger string value.

        Args:
            content: A chunk of file content to format.

        Returns:
            The JSON-escaped content string without surrounding quotes.

        Example:
            >>> strategy = JSONOutputStrategy()
            >>> print(strategy.format_content('line 1\\nprint("Hello")\\n'))
            line 1\\nprint(\\"Hello\\")\\n
            >>> print(strategy.format_content('path/with/\\backslash'))
            path/with/\\backslash
        """
        # Create a temporary dictionary with our content as a value to get proper JSON escaping
        temp_dict = {"content": content}
        # Encode the dictionary and extract just our escaped content
        json_str = self.encoder.encode(temp_dict)
        # Extract just the content portion (everything between the quotes)
        return json_str[len('{"content": "') : -2]  # noqa: E203

    def format_end(self, file_token_count: Optional[int] = None) -> str:
        """Format the end of the JSON object for a file.

        Closes the content string and the JSON object, optionally including the
        token count if one was provided in either format_start or format_end.

        Args:
            file_token_count: Token count to include in the output. If provided, must
                match any count provided in format_start.

        Returns:
            The closing portion of the JSON object.

        Raises:
            ValueError: If the token count doesn't match the one from format_start.

        Example:
            >>> strategy = JSONOutputStrategy()
            >>> # With token count
            >>> print(strategy.format_end(150))
            ", "tokens": 150}
            >>> # Without token count
            >>> strategy = JSONOutputStrategy()
            >>> print(strategy.format_end(None))
            "}
        """
        end = '"'
        if file_token_count is not None:
            if self.token_count is not None and self.token_count != file_token_count:
                raise ValueError(
                    "Non-matching token counts supplied at format_start and format_end: "
                    + f"'{self.token_count}' and '{file_token_count}'"
                )
            self.token_count = file_token_count
        if self.token_count is not None:
            end += f', "tokens": {self.token_count}'
        end += "}"
        return end

    def get_file_extension(self) -> str:
        """Get the file extension for JSON output.

        Returns:
            str: The string ".json".

        Example:
            >>> strategy = JSONOutputStrategy()
            >>> strategy.get_file_extension()
            '.json'
        """
        return ".json"
