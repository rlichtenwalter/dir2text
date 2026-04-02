"""Signal handling utilities for dir2text CLI.

This module provides signal handlers for managing interruptions
and ensuring proper cleanup during command-line operation.

SIGPIPE is only available on Unix-like systems. On Windows, the SIGPIPE
handler is not registered and sigpipe_received is never set, but the
interface remains consistent so callers don't need platform checks.
"""

import atexit
import os
import signal
import sys
from threading import Event
from types import FrameType
from typing import Any

_HAS_SIGPIPE = hasattr(signal, "SIGPIPE")


class SignalHandler:
    """Handles system signals for graceful interruption management.

    This class manages SIGPIPE and SIGINT signals to ensure proper cleanup and
    appropriate exit behavior when the program is interrupted.

    On Windows, SIGPIPE does not exist. The sigpipe_received event is still
    available but is never set, so callers can check it unconditionally.

    Attributes:
        sigpipe_received: Event that is set when a SIGPIPE signal is received.
        sigint_received: Event that is set when a SIGINT signal is received.
        original_sigpipe_handler: Original SIGPIPE signal handler, or None on Windows.
        original_sigint_handler: Original SIGINT signal handler.
    """

    def __init__(self) -> None:
        """Initialize signal handler with original handlers preserved."""
        self.sigpipe_received = Event()
        self.sigint_received = Event()
        self.original_sigpipe_handler: Any = signal.getsignal(signal.SIGPIPE) if _HAS_SIGPIPE else None
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)

    def handle_sigpipe(self, signum: int, frame: FrameType | None) -> None:
        """Handle SIGPIPE signal.

        Args:
            signum: The signal number.
            frame: The current stack frame.
        """
        self.sigpipe_received.set()
        if _HAS_SIGPIPE:
            signal.signal(signal.SIGPIPE, self.original_sigpipe_handler)

    def handle_sigint(self, signum: int, frame: FrameType | None) -> None:
        """Handle SIGINT signal.

        Args:
            signum: The signal number.
            frame: The current stack frame.
        """
        self.sigint_received.set()
        signal.signal(signal.SIGINT, self.original_sigint_handler)


# Create a singleton instance for the application
signal_handler = SignalHandler()


def setup_signal_handling() -> None:
    """Configure signal handlers for SIGPIPE and SIGINT.

    SIGPIPE handler is only registered on platforms that support it (Unix).
    SIGINT handler is registered on all platforms.
    """
    if _HAS_SIGPIPE:
        signal.signal(signal.SIGPIPE, signal_handler.handle_sigpipe)
    signal.signal(signal.SIGINT, signal_handler.handle_sigint)


def cleanup() -> None:
    """Cleanup function registered with atexit.

    Redirects stdout to the null device if we received SIGPIPE or SIGINT to prevent
    additional error messages during shutdown.
    """
    if signal_handler.sigpipe_received.is_set() or signal_handler.sigint_received.is_set():
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())


# Register the cleanup function
atexit.register(cleanup)
