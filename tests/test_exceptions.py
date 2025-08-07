"""Tests for custom exceptions."""

from dir2text.exceptions import BinaryFileError, TokenizationError, TokenizerNotAvailableError


class TestBinaryFileError:
    """Test BinaryFileError exception."""

    def test_binary_file_error_creation(self):
        """Test creating BinaryFileError with file path."""
        file_path = "/path/to/binary/file.bin"
        error = BinaryFileError(file_path)

        assert error.file_path == file_path
        assert str(error) == f"Binary file detected: {file_path}"

    def test_binary_file_error_attributes(self):
        """Test that BinaryFileError has the expected attributes."""
        file_path = "/another/binary/file.dat"
        error = BinaryFileError(file_path)

        assert hasattr(error, "file_path")
        assert error.file_path == file_path
        assert isinstance(error, Exception)


class TestExistingExceptions:
    """Test that existing exceptions still work as expected."""

    def test_tokenizer_not_available_error(self):
        """Test TokenizerNotAvailableError functionality."""
        error = TokenizerNotAvailableError()
        assert "Tokenizer (tiktoken) is not installed" in str(error)
        assert "pip install dir2text[token_counting]" in str(error)

    def test_tokenizer_not_available_error_custom_message(self):
        """Test TokenizerNotAvailableError with custom message."""
        custom_message = "Custom tokenizer error"
        error = TokenizerNotAvailableError(custom_message)
        assert custom_message in str(error)
        assert "pip install dir2text[token_counting]" in str(error)

    def test_tokenization_error(self):
        """Test TokenizationError functionality."""
        error = TokenizationError("Test tokenization failure")
        assert str(error) == "Test tokenization failure"
