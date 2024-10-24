"""Counter for tokens, lines, and characters in text content.

This module implements token counting using OpenAI's tiktoken library,
with support for counting lines and characters as well. Tokenization
uses either the cl100k_base or p50k_base encodings, which provide good
approximations for most modern language models.

Primary models and their encodings:
- GPT-4 models (gpt-4, gpt-4-32k) - cl100k_base encoding
- GPT-3.5-Turbo models (gpt-3.5-turbo) - cl100k_base encoding
- Text Davinci models (text-davinci-003) - p50k_base encoding

For other models, using a similar model's tokenizer (like gpt-4) can provide
useful approximations of token counts, though they may not exactly match
the target model's tokenization.
"""

import importlib.util
from collections import namedtuple
from typing import Any, Optional

from dir2text.exceptions import TokenizationError, TokenizerNotAvailableError

CountResult = namedtuple("CountResult", ["lines", "tokens", "characters"])


class TokenCounter:
    """Counter for tokens, lines, and characters in text content.

    This module implements token counting using OpenAI's tiktoken library,
    with support for counting lines and characters as well. If tiktoken is not
    installed, the counter will still function but will only count lines and
    characters, returning 0 for token counts.

    Tokenization uses either the cl100k_base or p50k_base encodings, which provide good
    approximations for most modern language models.

    Primary models and their encodings:
    - GPT-4 models (gpt-4, gpt-4-32k) - cl100k_base encoding
    - GPT-3.5-Turbo models (gpt-3.5-turbo) - cl100k_base encoding
    - Text Davinci models (text-davinci-003) - p50k_base encoding

    For other language models, using a similar model's tokenizer (like gpt-4) can provide
    useful approximations of token counts, though they may not exactly match
    the target model's tokenization. The default model 'gpt-4' uses cl100k_base encoding,
    which provides good general-purpose tokenization suitable for most modern LLMs.

    Attributes:
        model (str): Name of the model whose tokenizer to use.
        tiktoken_available (bool): Whether the tiktoken library is available.
        encoder (Optional[Any]): The tiktoken encoder if available, else None.

    Example:
        >>> counter = TokenCounter(model="gpt-4")
        >>> _ = counter.count("Hello\\nworld!")  # Count lines and characters (and tokens if available)

    Note:
        Token counting requires the tiktoken library to be installed via the 'token_counting'
        extra. If tiktoken is not installed, the counter will still function but will only
        count lines and characters, returning 0 for token counts. This behavior allows the
        counter to operate in environments where token counting is not required or where
        tiktoken cannot be installed.

    Raises:
        ValueError: If the specified model's tokenizer cannot be loaded.
        TokenizerNotAvailableError: If token counting is explicitly requested (by passing
            a model) but tiktoken is not installed.
    """

    def __init__(self, model: str = "gpt-4"):
        """Initialize the counter.

        Args:
            model: The model whose tokenizer to use. Defaults to "gpt-4", which provides
                a good general-purpose tokenization using the cl100k_base encoding.
                While primarily designed for OpenAI models, the tokenizers can provide
                useful approximations for similar models.

        Raises:
            ValueError: If the specified model's tokenizer cannot be loaded.
            TokenizerNotAvailableError: If tiktoken is not installed.
        """
        self.model = model
        self.tiktoken_available = self._check_tiktoken()
        self.encoder: Optional[Any] = None
        if self.tiktoken_available:
            try:
                self.encoder = self._get_encoder()
            except TokenizerNotAvailableError:
                self.tiktoken_available = False

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
        """Get the tiktoken encoder for the specified model.

        Returns:
            The tiktoken encoder instance.

        Raises:
            TokenizerNotAvailableError: If tiktoken is not installed.
            ValueError: If the specified model's tokenizer cannot be loaded.

        Note:
            The cl100k_base encoding (used by models like gpt-4) provides a good
            general-purpose tokenization that can approximate token counts for
            many modern language models.
        """
        if not self.tiktoken_available:
            raise TokenizerNotAvailableError()
        import tiktoken

        try:
            return tiktoken.encoding_for_model(self.model)
        except KeyError:
            raise ValueError(
                f"Could not load tokenizer for model '{self.model}'. Consider using a "
                "well-supported model like 'gpt-4' (cl100k_base encoding) or 'text-davinci-003' "
                "(p50k_base encoding) for token counting. While token counts may not exactly "
                "match your target model, they can provide useful approximations."
            )

    def count(self, text: str) -> CountResult:
        """Count lines, tokens, and characters in text.

        This method always counts lines and characters. It will also count tokens
        if the tiktoken library is available. All counts are added to running totals
        and also returned.

        Args:
            text: The text to analyze.

        Returns:
            CountResult: Named tuple containing:
                - lines: Number of newlines in this text
                - tokens: Number of tokens in this text (0 if token counting unavailable)
                - characters: Number of characters in this text

        Raises:
            TokenizationError: If token counting is available but fails.

        Example:
            >>> counter = TokenCounter()
            >>> result = counter.count("Hello\\nworld!")
            >>> result.lines
            1
            >>> result.characters
            12
            >>> result.tokens  # doctest: +SKIP
            3
        """
        lines = text.count("\n")
        chars = len(text)
        tokens = 0

        self._total_lines += lines
        self._total_characters += chars

        if self.tiktoken_available and self.encoder is not None:
            try:
                tokens = len(self.encoder.encode(text))
                self._total_tokens += tokens
            except Exception as e:
                # If token counting fails, we still keep the line and character counts
                # but we need to let the caller know about the tokenization failure
                raise TokenizationError(f"Failed to tokenize text: {str(e)}")

        return CountResult(lines=lines, tokens=tokens, characters=chars)

    def get_total_tokens(self) -> int:
        """Get the total number of tokens counted so far.

        Returns:
            Total tokens across all processed text.

        Example:
            >>> counter = TokenCounter()
            >>> _ = counter.count("Hello")
            >>> counter.get_total_tokens()  # doctest: +SKIP
            1
        """
        return self._total_tokens

    def get_total_lines(self) -> int:
        """Get the total number of lines counted so far.

        Returns:
            Total number of lines across all processed text.

        Example:
            >>> counter = TokenCounter()
            >>> _ = counter.count("line 1\\nline 2\\nline 3")
            >>> counter.get_total_lines()
            2
        """
        return self._total_lines

    def get_total_characters(self) -> int:
        """Get the total number of characters counted so far.

        Returns:
            Total character count across all processed text.

        Example:
            >>> counter = TokenCounter()
            >>> _ = counter.count("Hello\\n")
            >>> counter.get_total_characters()
            6
        """
        return self._total_characters

    def reset_counts(self) -> None:
        """Reset all running totals to zero.

        Resets token, line, and character counts while maintaining the same
        tokenizer configuration.

        Example:
            >>> counter = TokenCounter()
            >>> _ = counter.count("Some text")
            >>> counter.reset_counts()
            >>> counter.get_total_characters()
            0
        """
        self._total_tokens = 0
        self._total_lines = 0
        self._total_characters = 0
