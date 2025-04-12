"""Unit tests for the CLI main module with focus on tiktoken check."""

import contextlib
import io
from unittest.mock import patch

import pytest

from dir2text.cli.main import check_tiktoken_available, main


@pytest.fixture
def mock_tiktoken_available():
    """Mock tiktoken as available."""
    with patch("importlib.util.find_spec", return_value=True):
        yield


@pytest.fixture
def mock_tiktoken_unavailable():
    """Mock tiktoken as unavailable."""
    with patch("importlib.util.find_spec", return_value=None):
        yield


def test_check_tiktoken_available(mock_tiktoken_available):
    """Test the check_tiktoken_available function when tiktoken is available."""
    assert check_tiktoken_available() is True


def test_check_tiktoken_unavailable(mock_tiktoken_unavailable):
    """Test the check_tiktoken_available function when tiktoken is unavailable."""
    assert check_tiktoken_available() is False


def test_main_token_counting_without_tiktoken(mock_tiktoken_unavailable):
    """Test main function when token counting is requested but tiktoken is not available."""
    # Mock command line arguments to include -c flag
    with patch("sys.argv", ["dir2text", "-c", "."]), patch("sys.exit") as mock_exit:
        # Capture stderr
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            main()

        # Verify error message
        stderr_output = stderr.getvalue()
        assert "Error: Token counting was requested with -c/--count" in stderr_output
        assert 'pip install "dir2text[token_counting]"' in stderr_output
        assert 'poetry add "dir2text[token_counting]"' in stderr_output

        # Verify exit code
        mock_exit.assert_called_once_with(1)


def test_main_token_counting_with_tiktoken(mock_tiktoken_available):
    """Test main function when token counting is requested and tiktoken is available."""
    # Mock command line arguments and other dependencies to test the flow
    with (
        patch("sys.argv", ["dir2text", "-c", "."]),
        patch("dir2text.cli.argparser.create_parser"),
        patch("dir2text.cli.argparser.validate_args"),
        patch("dir2text.cli.main.StreamingDir2Text"),
        patch("dir2text.cli.main.SafeWriter"),
        patch("sys.exit"),
    ):

        # We need to handle other exceptions that might occur due to our mocking
        try:
            main()
        except Exception as e:
            # The important part is that it's not a TokenizerNotAvailableError
            assert "TokenizerNotAvailableError" not in str(type(e).__name__)
