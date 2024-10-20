import importlib.util
from typing import Optional

class TokenizerNotAvailableError(Exception):
    """Raised when the tokenizer (tiktoken) is not installed."""
    def __init__(self, message="Tokenizer (tiktoken) is not installed."):
        self.message = (
            f"{message} To enable token counting, install dir2text with the 'token_counting' "
            "extra: 'pip install dir2text[token_counting]' or 'poetry install --extras token_counting'."
        )
        super().__init__(self.message)

class TokenizationError(Exception):
    """Raised when tokenization fails."""
    pass

class TokenCounter:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.tiktoken_available = self._check_tiktoken()
        self.encoder = self._get_encoder() if self.tiktoken_available else None
        self._total_tokens = 0
        self._total_lines = 0
        self._total_characters = 0

    def _check_tiktoken(self) -> bool:
        return importlib.util.find_spec("tiktoken") is not None

    def _get_encoder(self):
        if not self.tiktoken_available:
            raise TokenizerNotAvailableError()
        import tiktoken
        try:
            return tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base if the model is not found
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        if not self.tiktoken_available or self.encoder is None:
            raise TokenizerNotAvailableError()
        try:
            token_count = len(self.encoder.encode(text))
            self._total_tokens += token_count
            self._total_lines += text.count('\n')
            self._total_characters += len(text)
            return token_count
        except Exception as e:
            raise TokenizationError(f"Failed to tokenize text: {str(e)}")

    def get_total_tokens(self) -> int:
        return self._total_tokens

    def get_total_lines(self) -> int:
        return self._total_lines

    def get_total_characters(self) -> int:
        return self._total_characters

    def reset_counts(self) -> None:
        self._total_tokens = 0
        self._total_lines = 0
        self._total_characters = 0