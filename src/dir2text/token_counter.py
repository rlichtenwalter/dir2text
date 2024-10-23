"""Counter for tokens, lines, and characters in text content.

This module provides token counting functionality using OpenAI's tiktoken library,
with support for tracking lines and characters as well.
"""

import importlib.util
from typing import Any, Optional

from dir2text.exceptions import TokenizationError, TokenizerNotAvailableError


class TokenCounter:
    """Counter for tokens, lines, and characters in text content.

    Uses OpenAI's tiktoken library to count tokens in a way that matches specific model
    tokenizers (e.g., GPT-4, GPT-3.5). Also tracks total lines and characters processed.
    The tiktoken library is an optional dependency that must be installed separately
    using the 'token_counting' extra.

    The counter maintains running totals of all metrics, allowing for incremental
    processing of content in chunks.

    Attributes:
        model (str): Name of the model whose tokenizer to emulate.
        tiktoken_available (bool): Whether the tiktoken library is available.
        encoder (Optional[Any]): The tiktoken encoder if available, else None.

    Example:
        >>> counter = TokenCounter(model="gpt-4")
        >>> counter.count_tokens("Hello")  # doctest: +SKIP
        1
        >>> counter.get_total_tokens()  # doctest: +SKIP
        1
        >>> counter.get_total_characters()  # doctest: +SKIP
        5
    """

    def __init__(self, model: str = "gpt-4"):
        """Initialize the token counter.

        Args:
            model: The model whose tokenizer to emulate. If the model
                is not found, falls back to 'cl100k_base' encoding.
                Defaults to "gpt-4".

        Example:
            >>> counter = TokenCounter()  # Uses gpt-4 tokenizer
            >>> counter = TokenCounter("gpt-3.5-turbo")  # Uses gpt-3.5 tokenizer
        """
        self.model = model
        self.tiktoken_available = self._check_tiktoken()
        self.encoder: Optional[Any] = self._get_encoder() if self.tiktoken_available else None
        self._total_tokens = 0
        self._total_lines = 0
        self._total_characters = 0

    def _check_tiktoken(self) -> bool:
        """Check if the tiktoken library is available.

        Returns:
            True if tiktoken is installed, False otherwise.
        """
        return importlib.util.find_spec("tiktoken") is not None

    def _get_encoder(self) -> Optional[Any]:
        """Get the appropriate tiktoken encoder for the specified model.

        Returns:
            The tiktoken encoder instance.

        Raises:
            TokenizerNotAvailableError: If tiktoken is not installed.

        Note:
            Falls back to 'cl100k_base' encoding if the specified model is not found.
        """
        if not self.tiktoken_available:
            raise TokenizerNotAvailableError()
        import tiktoken

        try:
            return tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base if the model is not found
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in the provided text and update running totals.

        Args:
            text: The text to tokenize and count.

        Returns:
            Number of tokens in the text.

        Raises:
            TokenizerNotAvailableError: If tiktoken is not installed.
            TokenizationError: If tokenization fails for any reason.

        Example:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("Hello\\nworld!")  # doctest: +SKIP
            3  # Tokens: ["Hello", "\\n", "world!"]
            >>> counter.get_total_lines()  # doctest: +SKIP
            1  # One newline character found
        """
        if not self.tiktoken_available or self.encoder is None:
            raise TokenizerNotAvailableError()
        try:
            token_count = len(self.encoder.encode(text))
            self._total_tokens += token_count
            self._total_lines += text.count("\n")
            self._total_characters += len(text)
            return token_count
        except Exception as e:
            raise TokenizationError(f"Failed to tokenize text: {str(e)}")

    def get_total_tokens(self) -> int:
        """Get the total number of tokens counted so far.

        Returns:
            Total tokens across all processed text.

        Example:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("Hello")  # doctest: +SKIP
            1
            >>> counter.count_tokens("world!")  # doctest: +SKIP
            2
            >>> counter.get_total_tokens()  # doctest: +SKIP
            3
        """
        return self._total_tokens

    def get_total_lines(self) -> int:
        """Get the total number of lines counted so far.

        A line is counted for each newline character encountered.

        Returns:
            Total number of lines across all processed text.

        Example:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("line 1\\nline 2\\nline 3")  # doctest: +SKIP
            6
            >>> counter.get_total_lines()  # doctest: +SKIP
            2  # Two newline characters
        """
        return self._total_lines

    def get_total_characters(self) -> int:
        """Get the total number of characters counted so far.

        Returns:
            Total character count across all processed text.

        Example:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("Hello\\n")  # doctest: +SKIP
            2  # Tokens: ["Hello", "\\n"]
            >>> counter.get_total_characters()  # doctest: +SKIP
            6  # Five letters plus newline
        """
        return self._total_characters

    def reset_counts(self) -> None:
        """Reset all running totals to zero.

        Resets token, line, and character counts while maintaining the same
        tokenizer configuration.

        Example:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("Some text")  # doctest: +SKIP
            2
            >>> counter.reset_counts()  # All counts return to 0
            >>> counter.get_total_tokens()  # doctest: +SKIP
            0
        """
        self._total_tokens = 0
        self._total_lines = 0
        self._total_characters = 0
