from unittest.mock import MagicMock, patch

import pytest

from dir2text.exceptions import TokenizationError
from dir2text.token_counter import CountResult, TokenCounter


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


def test_count(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        result = counter.count("Hello, world!")
        assert isinstance(result, CountResult)
        assert result.tokens == 13  # Based on our mock returning length of input
        assert result.lines == 0
        assert result.characters == 13
        assert counter.get_total_tokens() == 13
        assert counter.get_total_lines() == 0
        assert counter.get_total_characters() == 13


def test_count_tiktoken_unavailable(mock_tiktoken_unavailable):
    counter = TokenCounter()
    result = counter.count("Hello, world!")
    assert isinstance(result, CountResult)
    assert result.tokens == 0  # No tokens when tiktoken unavailable
    assert result.lines == 0
    assert result.characters == 13


def test_get_total_tokens(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count("Hello")
        counter.count("world!")
        assert counter.get_total_tokens() == 11


def test_get_total_lines(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count("Hello\nworld\n!")
        assert counter.get_total_lines() == 2


def test_get_total_characters(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count("Hello, world!")
        assert counter.get_total_characters() == 13


def test_reset_counts(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        counter.count("Hello, world!")
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
            counter.count("Hello, world!")


def test_count_empty_string(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        result = counter.count("")
        assert result.tokens == 0
        assert result.lines == 0
        assert result.characters == 0
        assert counter.get_total_tokens() == 0
        assert counter.get_total_lines() == 0
        assert counter.get_total_characters() == 0


def test_count_whitespace(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        result = counter.count("   \n\t\r  ")
        assert result.tokens == 8
        assert result.lines == 1
        assert result.characters == 8


def test_count_unicode(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        text = "Hello 世界! 🌍"  # Mixed ASCII, Unicode, and emoji
        result = counter.count(text)
        assert result.tokens == len(text)
        assert result.characters == len(text)


def test_count_control_chars(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        text = "Hello\x00World\x1F!"  # Text with control characters
        result = counter.count(text)
        assert result.tokens == len(text)
        assert result.characters == len(text)


def test_count_very_long_text(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        long_text = "x" * 1_000_000  # Test with a million characters
        result = counter.count(long_text)
        assert result.tokens == 1_000_000
        assert result.characters == 1_000_000


def test_model_support_behavior(mock_tiktoken_available):
    """Test behavior with supported and unsupported model specifications."""
    with patch("tiktoken.encoding_for_model") as mock_encoding_for_model:
        # Test unsupported model
        mock_encoding_for_model.side_effect = KeyError("Model not found")
        with pytest.raises(ValueError) as exc_info:
            counter = TokenCounter(model="nonexistent_model")
            _ = counter.count("test")

        # Verify error message is helpful
        assert "cl100k_base" in str(exc_info.value)
        assert "p50k_base" in str(exc_info.value)

        # Test supported model
        mock_encoding_for_model.side_effect = None
        mock_encoding_for_model.return_value = MagicMock(encode=lambda x: [0] * len(x))

        counter = TokenCounter(model="gpt-4")
        result = counter.count("test")
        assert result.tokens == 4

        # Verify the mock was called with correct model
        mock_encoding_for_model.assert_called_with("gpt-4")


def test_count_accumulation(mock_tiktoken_available, mock_encoder):
    """Test that counts accumulate correctly across multiple calls."""
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()

        # First count
        result1 = counter.count("Hello\n")
        assert result1 == CountResult(lines=1, tokens=6, characters=6)
        assert counter.get_total_lines() == 1
        assert counter.get_total_tokens() == 6
        assert counter.get_total_characters() == 6

        # Second count
        result2 = counter.count("World!\n")
        assert result2 == CountResult(lines=1, tokens=7, characters=7)
        assert counter.get_total_lines() == 2
        assert counter.get_total_tokens() == 13
        assert counter.get_total_characters() == 13


def test_count_accumulation_without_tiktoken(mock_tiktoken_unavailable):
    """Test accumulation without token counting available."""
    counter = TokenCounter()

    # First count
    result1 = counter.count("Hello\n")
    assert result1 == CountResult(lines=1, tokens=0, characters=6)
    assert counter.get_total_lines() == 1
    assert counter.get_total_tokens() == 0
    assert counter.get_total_characters() == 6

    # Second count
    result2 = counter.count("World!\n")
    assert result2 == CountResult(lines=1, tokens=0, characters=7)
    assert counter.get_total_lines() == 2
    assert counter.get_total_tokens() == 0
    assert counter.get_total_characters() == 13


def test_reset_counts_between_uses(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()

        # First use
        result1 = counter.count("Hello\n")
        assert result1.tokens == 6

        # Reset and second use
        counter.reset_counts()
        result2 = counter.count("World")
        assert result2.tokens == 5  # Should not include previous counts
        assert counter.get_total_tokens() == 5  # Should only reflect second count
