"""Unit tests for the signal handler module in dir2text CLI."""

import os
import signal
import sys
from unittest.mock import MagicMock, patch

import pytest

from dir2text.cli.signal_handler import SignalHandler, cleanup, setup_signal_handling, signal_handler


@pytest.fixture
def mock_signal():
    """Create a mock for the signal module."""
    # We need to patch the actual signal module that's imported in the signal_handler module
    with patch("signal.signal", autospec=True) as mock:
        yield mock


@pytest.fixture
def mock_os():
    """Create a mock for os module functions used in signal handling."""
    with patch("dir2text.cli.signal_handler.os", autospec=True) as mock:
        # Setup specific mocks for functions used
        mock.open.return_value = 123  # Mock file descriptor
        mock.dup2 = MagicMock()
        mock.devnull = "/dev/null"  # Ensure devnull is properly mocked
        mock.O_WRONLY = os.O_WRONLY  # Keep the real value
        yield mock


@pytest.fixture
def fresh_signal_handler():
    """Create a fresh SignalHandler instance for tests.

    This avoids interference with the singleton instance.
    """
    return SignalHandler()


def test_signal_handler_initialization():
    """Test SignalHandler initialization."""
    with patch("signal.getsignal") as mock_getsignal:
        # Set up return values for getsignal
        mock_getsignal.side_effect = [
            lambda sig, frame: None,  # For SIGPIPE
            lambda sig, frame: None,  # For SIGINT
        ]

        handler = SignalHandler()

        # Verify signal handlers were retrieved
        assert mock_getsignal.call_count == 2
        mock_getsignal.assert_any_call(signal.SIGPIPE)
        mock_getsignal.assert_any_call(signal.SIGINT)

        # Verify attributes were set
        assert not handler.sigpipe_received.is_set()
        assert not handler.sigint_received.is_set()
        assert handler.original_sigpipe_handler is not None
        assert handler.original_sigint_handler is not None


def test_handle_sigpipe(fresh_signal_handler, mock_signal):
    """Test the SIGPIPE handler function."""
    # Mock a frame instead of trying to create one, which is not possible
    mock_frame = MagicMock()

    # Set up the mock for the original handler
    with patch("signal.signal", mock_signal):
        # Call the handler
        fresh_signal_handler.handle_sigpipe(signal.SIGPIPE, mock_frame)

        # Verify the event was set
        assert fresh_signal_handler.sigpipe_received.is_set()

        # Verify the original handler was restored
        mock_signal.assert_called_once_with(signal.SIGPIPE, fresh_signal_handler.original_sigpipe_handler)


def test_handle_sigint(fresh_signal_handler, mock_signal):
    """Test the SIGINT handler function."""
    # Mock a frame instead of trying to create one, which is not possible
    mock_frame = MagicMock()

    # Set up the mock for the original handler
    with patch("signal.signal", mock_signal):
        # Call the handler
        fresh_signal_handler.handle_sigint(signal.SIGINT, mock_frame)

        # Verify the event was set
        assert fresh_signal_handler.sigint_received.is_set()

        # Verify the original handler was restored
        mock_signal.assert_called_once_with(signal.SIGINT, fresh_signal_handler.original_sigint_handler)


def test_setup_signal_handling(mock_signal):
    """Test signal handler setup function."""
    # Clear any previous calls to the mock to avoid interference
    mock_signal.reset_mock()

    # We need to use the right patch path when testing the function directly
    with patch("signal.signal", mock_signal):
        setup_signal_handling()

    # Verify signal handlers were set
    assert mock_signal.call_count == 2
    mock_signal.assert_any_call(signal.SIGPIPE, signal_handler.handle_sigpipe)
    mock_signal.assert_any_call(signal.SIGINT, signal_handler.handle_sigint)


def test_cleanup_with_no_signals(mock_os):
    """Test cleanup function when no signals were received."""
    # Save original state
    original_sigpipe = signal_handler.sigpipe_received.is_set()
    original_sigint = signal_handler.sigint_received.is_set()

    # Ensure both flags are False
    signal_handler.sigpipe_received.clear()
    signal_handler.sigint_received.clear()

    try:
        cleanup()

        # Verify no redirections happened
        mock_os.open.assert_not_called()
        mock_os.dup2.assert_not_called()
    finally:
        # Restore original state
        if original_sigpipe:
            signal_handler.sigpipe_received.set()
        else:
            signal_handler.sigpipe_received.clear()

        if original_sigint:
            signal_handler.sigint_received.set()
        else:
            signal_handler.sigint_received.clear()


def test_cleanup_with_sigpipe(mock_os):
    """Test cleanup function when SIGPIPE was received."""
    # Save original state
    original_sigpipe = signal_handler.sigpipe_received.is_set()
    original_sigint = signal_handler.sigint_received.is_set()

    try:
        # Set the SIGPIPE flag
        signal_handler.sigpipe_received.set()
        signal_handler.sigint_received.clear()

        # Mock stdout fileno
        with patch.object(sys, "stdout") as mock_stdout:
            mock_stdout.fileno.return_value = 1
            cleanup()

        # Verify redirection to /dev/null
        mock_os.open.assert_called_once_with(os.devnull, os.O_WRONLY)
        mock_os.dup2.assert_called_once_with(123, 1)  # 123 is the mock fd, 1 is stdout
    finally:
        # Restore original state
        if original_sigpipe:
            signal_handler.sigpipe_received.set()
        else:
            signal_handler.sigpipe_received.clear()

        if original_sigint:
            signal_handler.sigint_received.set()
        else:
            signal_handler.sigint_received.clear()


def test_cleanup_with_sigint(mock_os):
    """Test cleanup function when SIGINT was received."""
    # Save original state
    original_sigpipe = signal_handler.sigpipe_received.is_set()
    original_sigint = signal_handler.sigint_received.is_set()

    try:
        # Set the SIGINT flag
        signal_handler.sigpipe_received.clear()
        signal_handler.sigint_received.set()

        # Mock stdout fileno
        with patch.object(sys, "stdout") as mock_stdout:
            mock_stdout.fileno.return_value = 1
            cleanup()

        # Verify redirection to /dev/null
        mock_os.open.assert_called_once_with(os.devnull, os.O_WRONLY)
        mock_os.dup2.assert_called_once_with(123, 1)  # 123 is the mock fd, 1 is stdout
    finally:
        # Restore original state
        if original_sigpipe:
            signal_handler.sigpipe_received.set()
        else:
            signal_handler.sigpipe_received.clear()

        if original_sigint:
            signal_handler.sigint_received.set()
        else:
            signal_handler.sigint_received.clear()


def test_singleton_instance():
    """Test that the provided singleton instance is properly initialized."""
    # The imported signal_handler should already be initialized
    assert isinstance(signal_handler, SignalHandler)
    assert signal_handler.sigpipe_received is not None
    assert signal_handler.sigint_received is not None
    assert hasattr(signal_handler, "original_sigpipe_handler")
    assert hasattr(signal_handler, "original_sigint_handler")


def test_atexit_registration():
    """Test that the cleanup function is registered with atexit."""
    with patch("atexit.register") as mock_register:
        # Re-import the module to trigger registration
        from importlib import reload

        from dir2text.cli import signal_handler as test_module

        reload(test_module)
        mock_register.assert_called_once_with(test_module.cleanup)
