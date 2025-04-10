"""Safe output writing utilities for dir2text CLI.

This module provides a safe writing interface that handles
signals and interruptions gracefully.
"""

import errno
import os
import types
from pathlib import Path
from typing import Optional, Type, Union

from dir2text.cli.signal_handler import signal_handler


class SafeWriter:
    """Safe writing interface for handling output with signal awareness.

    This class provides a safe way to write output while being aware of
    signals that might interrupt the process. It handles both file and
    file descriptor outputs.

    Attributes:
        file: Either a file path or file descriptor for output.
        fd: The actual file descriptor being written to.
    """

    def __init__(self, file: Union[int, Path]):
        """Initialize the safe writer.

        Args:
            file: Either a file descriptor (int) or Path object for writing output.
        """
        self.file = file
        self._closed = False

        if isinstance(file, int):
            # It's already a file descriptor
            self.fd = file
            self._file_obj = None
        elif isinstance(file, (str, os.PathLike)):
            path = Path(file)
            self._file_obj = path.open("w")
            self.fd = self._file_obj.fileno()
        else:
            raise TypeError(f"Expected int, str, or PathLike, got {type(file).__name__}")

    def write(self, data: str) -> None:
        """Safely write data with signal checking.

        Args:
            data: String data to write.

        Raises:
            BrokenPipeError: If SIGPIPE received or pipe is broken.
            OSError: If an I/O error occurs during writing.
            ValueError: If attempting to write to a closed writer.
        """
        if self._closed:
            raise ValueError("Cannot write to closed SafeWriter")

        if signal_handler.sigpipe_received.is_set() or signal_handler.sigint_received.is_set():
            raise BrokenPipeError()

        try:
            os.write(self.fd, data.encode("utf-8"))
        except OSError as e:
            if e.errno == errno.EPIPE:
                raise BrokenPipeError()
            raise

    def close(self) -> None:
        """Close the file descriptor if it was opened by this class.

        This method ensures the writer is marked as closed even if the
        underlying close operation fails with a broken pipe error.
        """
        if self._closed:
            return

        if self._file_obj is not None:
            try:
                self._file_obj.close()
            except OSError as e:
                # Handle broken pipe errors during close gracefully
                if e.errno != errno.EPIPE:
                    # Re-raise errors that aren't related to broken pipes
                    raise
                # For broken pipe errors, continue and mark as closed

        self._closed = True

    def __enter__(self) -> "SafeWriter":
        """Enter the context manager.

        Returns:
            self: The SafeWriter instance for use in the with block.
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        """Exit the context manager and close resources.

        If an exception occurs during the close operation and there was
        already an exception in the with block, the original exception is
        prioritized.

        Args:
            exc_type: The exception type, if an exception was raised.
            exc_val: The exception value, if an exception was raised.
            exc_tb: The exception traceback, if an exception was raised.
        """
        try:
            self.close()
        except OSError:
            # Only suppress close errors if there was already an exception
            if exc_type is None:
                raise
            # If there was already an exception, prioritize it
