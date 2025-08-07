class TokenizerNotAvailableError(Exception):
    """
    Exception raised when attempting to use token counting functionality without the required tokenizer package.

    This exception is raised when the `tiktoken` package is not installed but token counting
    functionality is requested. The tiktoken package is an optional dependency that must be
    explicitly installed using the 'token_counting' extra.

    Attributes:
        message (str): Detailed error message including installation instructions.

    Example:
        >>> error = TokenizerNotAvailableError()
        >>> str(error).startswith('Tokenizer (tiktoken) is not installed')
        True
    """

    def __init__(self, message: str = "Tokenizer (tiktoken) is not installed.") -> None:
        """
        Initialize the exception with an informative error message.

        Args:
            message (str, optional): Base error message. Defaults to "Tokenizer (tiktoken) is not installed."
                Installation instructions will be appended to this message.
        """
        self.message = (
            f"{message} To enable token counting, install dir2text with the 'token_counting' "
            "extra: 'pip install dir2text[token_counting]' or 'poetry install --extras token_counting'."
        )
        super().__init__(self.message)


class TokenizationError(Exception):
    """
    Exception raised when token counting fails during execution.

    This exception is raised when the tokenizer is available but fails to process the input text.
    This can happen due to invalid input, encoding errors, or other issues with the tokenization
    process.

    Example:
        >>> error = TokenizationError("Failed to tokenize: invalid input")
        >>> str(error)
        'Failed to tokenize: invalid input'
    """

    pass


class BinaryFileError(Exception):
    """
    Exception raised when a binary file is encountered and binary_action is RAISE.

    This exception is raised when a binary file is detected during content processing
    and the configured binary action is set to RAISE (which maps to either warn or fail
    at the CLI level).

    Attributes:
        file_path (str): Path to the binary file that was encountered.

    Example:
        >>> error = BinaryFileError("/path/to/binary.dat")
        >>> str(error)
        'Binary file detected: /path/to/binary.dat'
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialize the exception with the path to the binary file.

        Args:
            file_path (str): Path to the binary file that was encountered.
        """
        self.file_path = file_path
        super().__init__(f"Binary file detected: {file_path}")
