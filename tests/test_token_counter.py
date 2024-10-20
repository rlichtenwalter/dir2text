import pytest
from unittest.mock import patch, MagicMock
from dir2text.token_counter import TokenCounter, TokenizerNotAvailableError, TokenizationError


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


def test_count_tokens_tiktoken_unavailable(mock_tiktoken_unavailable):
    counter = TokenCounter()
    with pytest.raises(TokenizerNotAvailableError):
        counter.count_tokens("Hello, world!")


def test_count_tokens_batch(mock_tiktoken_available, mock_encoder):
    with patch("tiktoken.encoding_for_model", return_value=mock_encoder):
        counter = TokenCounter()
        texts = ["Hello", "world", "!"]
        assert counter.count_tokens_batch(texts) == [5, 5, 1]


def test_count_tokens_batch_tiktoken_unavailable(mock_tiktoken_unavailable):
    counter = TokenCounter()
    with pytest.raises(TokenizerNotAvailableError):
        counter.count_tokens_batch(["Hello", "world", "!"])


def test_count_lines():
    counter = TokenCounter()
    text = "Hello\nworld\n!"
    assert counter.count_lines(text) == 3


def test_count_characters():
    counter = TokenCounter()
    text = "Hello, world!"
    assert counter.count_characters(text) == 13


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
