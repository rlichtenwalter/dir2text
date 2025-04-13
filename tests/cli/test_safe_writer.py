"""Unit tests for the SafeWriter class in dir2text CLI."""

import errno
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dir2text.cli.safe_writer import SafeWriter


@pytest.fixture
def mock_signals():
    """Create a mock for signal handler checks."""
    with patch("dir2text.cli.safe_writer.signal_handler") as mock:
        mock.sigpipe_received = MagicMock()
        mock.sigpipe_received.is_set.return_value = False
        mock.sigint_received = MagicMock()
        mock.sigint_received.is_set.return_value = False
        yield mock


@pytest.fixture
def temp_output_file():
    """Create a temporary file for testing file output."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        yield f.name
    # Clean up the file after tests
    if os.path.exists(f.name):
        os.unlink(f.name)


def test_safe_writer_init_with_fd():
    """Test SafeWriter initialization with a file descriptor."""
    # Use a mock file descriptor
    fd = 3

    writer = SafeWriter(fd)

    # Check attributes
    assert writer.file == fd
    assert writer.fd == fd
    assert writer._file_obj is None
    assert not writer._closed


def test_safe_writer_init_with_path_string():
    """Test SafeWriter initialization with a path string."""
    # Mock the file open operation
    with patch("pathlib.Path.open") as mock_open_func:
        mock_file = MagicMock()
        mock_file.fileno.return_value = 5
        mock_open_func.return_value = mock_file

        writer = SafeWriter("/path/to/file.txt")

        # Check attributes - convert both to Path objects for comparison
        assert Path(writer.file) == Path("/path/to/file.txt")
        assert writer.fd == 5
        assert writer._file_obj is mock_file
        assert not writer._closed


def test_safe_writer_init_with_path_object():
    """Test SafeWriter initialization with a Path object."""
    # Mock the file open operation
    with patch("pathlib.Path.open") as mock_open_func:
        mock_file = MagicMock()
        mock_file.fileno.return_value = 5
        mock_open_func.return_value = mock_file

        path = Path("/path/to/file.txt")
        writer = SafeWriter(path)

        # Check attributes
        assert writer.file == path
        assert writer.fd == 5
        assert writer._file_obj is mock_file
        assert not writer._closed


def test_safe_writer_init_with_invalid_type():
    """Test SafeWriter initialization with an invalid type."""
    with pytest.raises(TypeError) as excinfo:
        SafeWriter(42.0)  # Float is not a valid type

    assert "Expected int, str, or PathLike" in str(excinfo.value)


def test_safe_writer_write(mock_signals):
    """Test SafeWriter.write method with normal conditions."""
    with patch("os.write") as mock_write:
        writer = SafeWriter(3)  # Use fd 3
        writer.write("test data")

        # Check that os.write was called with correct args
        mock_write.assert_called_once_with(3, b"test data")


def test_safe_writer_write_after_close():
    """Test SafeWriter.write method after closing."""
    writer = SafeWriter(3)  # Use fd 3
    writer._closed = True

    with pytest.raises(ValueError) as excinfo:
        writer.write("test data")

    assert "Cannot write to closed SafeWriter" in str(excinfo.value)


def test_safe_writer_write_with_sigpipe(mock_signals):
    """Test SafeWriter.write method with SIGPIPE received."""
    # Set up the signal handler mock to indicate SIGPIPE
    mock_signals.sigpipe_received.is_set.return_value = True

    writer = SafeWriter(3)  # Use fd 3

    with pytest.raises(BrokenPipeError):
        writer.write("test data")


def test_safe_writer_write_with_sigint(mock_signals):
    """Test SafeWriter.write method with SIGINT received."""
    # Set up the signal handler mock to indicate SIGINT
    mock_signals.sigint_received.is_set.return_value = True

    writer = SafeWriter(3)  # Use fd 3

    with pytest.raises(BrokenPipeError):
        writer.write("test data")


def test_safe_writer_write_with_os_error():
    """Test SafeWriter.write method with an OSError (not EPIPE)."""
    with patch("os.write") as mock_write:
        # Set up os.write to raise a non-EPIPE error
        mock_write.side_effect = OSError(errno.EIO, "Input/output error")

        writer = SafeWriter(3)  # Use fd 3

        with pytest.raises(OSError) as excinfo:
            writer.write("test data")

        assert excinfo.value.errno == errno.EIO


def test_safe_writer_write_with_epipe():
    """Test SafeWriter.write method with an EPIPE error."""
    with patch("os.write") as mock_write:
        # Set up os.write to raise an EPIPE error
        mock_write.side_effect = OSError(errno.EPIPE, "Broken pipe")

        writer = SafeWriter(3)  # Use fd 3

        with pytest.raises(BrokenPipeError):
            writer.write("test data")


def test_safe_writer_close_fd_only():
    """Test SafeWriter.close method with file descriptor only."""
    writer = SafeWriter(3)  # Use fd 3
    writer.close()

    # Should just mark as closed, no file to close
    assert writer._closed


def test_safe_writer_close_with_file():
    """Test SafeWriter.close method with file object."""
    # Create a mock file object
    mock_file = MagicMock()

    writer = SafeWriter(3)  # Use fd 3
    writer._file_obj = mock_file
    writer.close()

    # Should close the file and mark as closed
    mock_file.close.assert_called_once()
    assert writer._closed


def test_safe_writer_close_twice():
    """Test SafeWriter.close method called twice."""
    # Create a mock file object
    mock_file = MagicMock()

    writer = SafeWriter(3)  # Use fd 3
    writer._file_obj = mock_file
    writer.close()
    writer.close()  # Second close should be a no-op

    # Should only close once
    mock_file.close.assert_called_once()
    assert writer._closed


def test_safe_writer_actual_file_write(temp_output_file):
    """Test SafeWriter writing to an actual file."""
    writer = SafeWriter(temp_output_file)
    test_data = "Hello, world!\nTest line 2."

    writer.write(test_data)
    writer.close()

    # Read the file and verify content
    with open(temp_output_file, "r") as f:
        content = f.read()

    assert content == test_data


def test_safe_writer_unicode_handling(temp_output_file):
    """Test SafeWriter handling Unicode characters."""
    writer = SafeWriter(temp_output_file)
    # Mix of ASCII, Unicode, and emojis
    test_data = "Hello, 世界! 🌍 Café"

    writer.write(test_data)
    writer.close()

    # Read the file and verify content
    with open(temp_output_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert content == test_data


def test_safe_writer_context_manager():
    """Test SafeWriter used as a context manager.

    This test verifies that SafeWriter can be used in a with statement.
    """
    # Mock a file descriptor for testing
    fd = 3

    # Use SafeWriter as a context manager
    with SafeWriter(fd) as writer:
        assert writer.fd == fd
        assert not writer._closed

    # Verify it's closed after exiting the context
    assert writer._closed


def test_safe_writer_context_manager_with_exception():
    """Test SafeWriter context manager with an exception in the with block."""
    # Mock a file descriptor for testing
    fd = 3

    try:
        with SafeWriter(fd) as writer:
            assert not writer._closed
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify it's closed even after an exception
    assert writer._closed


def test_safe_writer_close_with_error():
    """Test SafeWriter.close method handling errors."""
    # Create a mock file object that raises an error on close
    mock_file = MagicMock()
    mock_file.close.side_effect = OSError(errno.EIO, "I/O error")

    writer = SafeWriter(3)  # Use fd 3
    writer._file_obj = mock_file

    # Should raise the error since it's not a broken pipe error
    with pytest.raises(OSError) as excinfo:
        writer.close()

    assert excinfo.value.errno == errno.EIO
    mock_file.close.assert_called_once()


def test_safe_writer_close_with_broken_pipe():
    """Test SafeWriter.close method handling broken pipe errors."""
    # Create a mock file object that raises a broken pipe error on close
    mock_file = MagicMock()
    mock_file.close.side_effect = OSError(errno.EPIPE, "Broken pipe")

    writer = SafeWriter(3)  # Use fd 3
    writer._file_obj = mock_file

    # Should handle the broken pipe error and still mark as closed
    writer.close()

    assert writer._closed
    mock_file.close.assert_called_once()
