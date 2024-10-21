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
