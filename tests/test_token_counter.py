from unittest.mock import MagicMock, patch

import pytest

from dir2text.exceptions import TokenizationError, TokenizerNotAvailableError
from dir2text.token_counter import TokenCounter


@pytest.fixture
def mock_tiktoken_available():
    with patch("importlib.util.find_spec", return_value=True):
        yield


@pytest.fixture
def mock_tiktoken_unavailable():
    with patch("importlib.util.find_spec", return_value=None):
        yield


@pytest.fixture
def mock_encoder():
    encoder = MagicMock()
    encoder.encode.side_effect = lambda text: [0] * len(text)  # Mock tokenization
    return encoder


def test_token_counter_initialization(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        assert counter.tiktoken_available
        assert counter.encoder is not None


def test_token_counter_initialization_tiktoken_unavailable(mock_tiktoken_unavailable):
    counter = TokenCounter()
    assert not counter.tiktoken_available
    assert counter.encoder is None


def test_count_tokens(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        assert counter.count_tokens("Hello, world!") == 13
        assert counter.get_total_tokens() == 13
        assert counter.get_total_lines() == 0
        assert counter.get_total_characters() == 13


def test_count_tokens_tiktoken_unavailable(mock_tiktoken_unavailable):
    counter = TokenCounter()
    with pytest.raises(TokenizerNotAvailableError):
        counter.count_tokens("Hello, world!")


def test_get_total_tokens(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count_tokens("Hello")
        counter.count_tokens("world!")
        assert counter.get_total_tokens() == 11


def test_get_total_lines(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count_tokens("Hello\nworld\n!")
        assert counter.get_total_lines() == 2


def test_get_total_characters(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count_tokens("Hello, world!")
        assert counter.get_total_characters() == 13


def test_reset_counts(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count_tokens("Hello, world!")
        counter.reset_counts()
        assert counter.get_total_tokens() == 0
        assert counter.get_total_lines() == 0
        assert counter.get_total_characters() == 0


def test_tokenization_error(mock_tiktoken_available):
    with patch("tiktoken.encoding_for_model") as mock_encoding:
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = Exception("Tokenization failed")
        mock_encoding.return_value = mock_encoder

        counter = TokenCounter()
        with pytest.raises(TokenizationError):
            counter.count_tokens("Hello, world!")


def test_model_not_found_fallback(mock_tiktoken_available):
    with patch("tiktoken.encoding_for_model", side_effect=KeyError), patch(
        "tiktoken.get_encoding"
    ) as mock_get_encoding:
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = lambda text: [0] * len(text)
        mock_get_encoding.return_value = mock_encoder

        counter = TokenCounter(model="non_existent_model")
        assert counter.count_tokens("Hello, world!") == 13


def test_count_tokens_empty_string(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        assert counter.count_tokens("") == 0
        assert counter.get_total_tokens() == 0
        assert counter.get_total_lines() == 0
        assert counter.get_total_characters() == 0


def test_count_tokens_whitespace(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        assert counter.count_tokens("   \n\t\r  ") == 8
        assert counter.get_total_lines() == 1
        assert counter.get_total_characters() == 8


def test_count_tokens_unicode(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        text = "Hello 世界! 🌍"  # Mixed ASCII, Unicode, and emoji
        assert counter.count_tokens(text) == len(text)
        assert counter.get_total_characters() == len(text)


def test_count_tokens_control_chars(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        text = "Hello\x00World\x1F!"  # Text with control characters
        assert counter.count_tokens(text) == len(text)
        assert counter.get_total_characters() == len(text)


def test_count_tokens_very_long_text(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        long_text = "x" * 1_000_000  # Test with a million characters
        assert counter.count_tokens(long_text) == 1_000_000
        assert counter.get_total_characters() == 1_000_000


def test_multiple_model_fallbacks(mock_tiktoken_available):
    # Test multiple model fallback scenarios
    with patch("tiktoken.encoding_for_model") as mock_encoding_for_model, patch(
        "tiktoken.get_encoding"
    ) as mock_get_encoding:

        # First call raises KeyError, second succeeds
        mock_encoding_for_model.side_effect = [KeyError("Model not found"), MagicMock(encode=lambda x: [0] * len(x))]
        mock_get_encoding.return_value = MagicMock(encode=lambda x: [0] * len(x))

        counter = TokenCounter(model="nonexistent_model")
        assert counter.count_tokens("test") == 4


def test_consecutive_counts_accumulation(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()

        # Test that counts accumulate correctly across multiple calls
        counter.count_tokens("Hello\n")  # 6 chars, 1 line
        counter.count_tokens("World\n")  # 6 chars, 1 line
        counter.count_tokens("!")  # 1 char, 0 lines

        assert counter.get_total_tokens() == 13
        assert counter.get_total_lines() == 2
        assert counter.get_total_characters() == 13


def test_reset_counts_between_uses(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()

        # First use
        counter.count_tokens("Hello\n")
        assert counter.get_total_tokens() == 6

        # Reset and second use
        counter.reset_counts()
        counter.count_tokens("World")
        assert counter.get_total_tokens() == 5  # Should not include previous counts
