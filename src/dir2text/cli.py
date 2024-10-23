"""Command-line interface for dir2text.

This module provides the command-line interface for dir2text, allowing users to generate
tree representations and file contents from directories. It handles command-line argument
parsing, output formatting, and signal management for graceful interruption handling.

Key Features:
    - Directory tree visualization
    - File content output in XML or JSON format
    - Token counting with model selection
    - Signal handling (SIGPIPE, SIGINT)
    - Exclusion rule support (e.g., .gitignore patterns)
    - Output redirection and file writing
    - Various output format options and combinations

Signal Handling Notes:
    The module implements careful signal handling to ensure proper cleanup on interruption:
    - SIGPIPE: Handled when output pipe is closed (e.g., when piping to `head`)
    - SIGINT: Handled for clean exit on Ctrl+C
    Both cases ensure proper cleanup and appropriate exit codes.

Exit Codes:
    0: Successful completion
    1: Runtime error during execution
    2: Command-line syntax error
    130: Interrupted by SIGINT (Ctrl+C)
    141: Broken pipe (SIGPIPE)

Example:
    # Basic usage to process a directory
    $ dir2text /path/to/dir

    # With exclusions and token counting
    $ dir2text /path/to/dir -e .gitignore -c -t gpt-4
"""

import argparse
import atexit
import errno
import os
import signal
import sys
from collections.abc import Mapping
from pathlib import Path
from threading import Event
from types import FrameType
from typing import Optional, Union

from dir2text.dir2text import StreamingDir2Text


class SignalHandler:
    """Handles system signals for graceful interruption management.

    This class manages SIGPIPE and SIGINT signals to ensure proper cleanup and
    appropriate exit behavior when the program is interrupted.

    Attributes:
        sigpipe_received: Event that is set when a SIGPIPE signal is received.
        sigint_received: Event that is set when a SIGINT signal is received.
        original_sigpipe_handler: Original SIGPIPE signal handler.
        original_sigint_handler: Original SIGINT signal handler.
    """

    def __init__(self) -> None:
        """Initialize signal handler with original handlers preserved."""
        self.sigpipe_received = Event()
        self.sigint_received = Event()
        self.original_sigpipe_handler = signal.getsignal(signal.SIGPIPE)
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)

    def handle_sigpipe(self, signum: int, frame: Optional[FrameType]) -> None:
        """Handle SIGPIPE signal.

        Args:
            signum: The signal number.
            frame: The current stack frame.
        """
        self.sigpipe_received.set()
        signal.signal(signal.SIGPIPE, self.original_sigpipe_handler)

    def handle_sigint(self, signum: int, frame: Optional[FrameType]) -> None:
        """Handle SIGINT signal.

        Args:
            signum: The signal number.
            frame: The current stack frame.
        """
        self.sigint_received.set()
        signal.signal(signal.SIGINT, self.original_sigint_handler)


signal_handler = SignalHandler()


def setup_signal_handling() -> None:
    """Configure signal handlers for SIGPIPE and SIGINT."""
    signal.signal(signal.SIGPIPE, signal_handler.handle_sigpipe)
    signal.signal(signal.SIGINT, signal_handler.handle_sigint)


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
        self.fd = file if isinstance(file, int) else file.open("w").fileno()

    def write(self, data: str) -> None:
        """Safely write data with signal checking.

        Args:
            data: String data to write.

        Raises:
            BrokenPipeError: If SIGPIPE received or pipe is broken.
            OSError: If an I/O error occurs during writing.
        """
        if signal_handler.sigpipe_received.is_set() or signal_handler.sigint_received.is_set():
            raise BrokenPipeError()
        try:
            os.write(self.fd, data.encode())
        except OSError as e:
            if e.errno == errno.EPIPE:
                raise BrokenPipeError()
            raise

    def close(self) -> None:
        """Close the file descriptor if it was opened by this class."""
        if not isinstance(self.file, int):
            os.close(self.fd)


def cleanup() -> None:
    """Cleanup function registered with atexit.

    Redirects stdout to /dev/null if we received SIGPIPE or SIGINT to prevent
    additional error messages during shutdown.
    """
    if signal_handler.sigpipe_received.is_set() or signal_handler.sigint_received.is_set():
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())


atexit.register(cleanup)


def format_counts(counts: Mapping[str, Optional[int]]) -> str:
    """Format the counts into a human-readable string.

    Args:
        counts: Mapping containing various count metrics. Expected keys are:
            - 'directories': Number of directories (int).
            - 'files': Number of files (int).
            - 'lines': Number of lines (int).
            - 'characters': Number of characters (int).
            - 'tokens': Optional number of tokens (Optional[int]).
                May be None if token counting is not available.

    Returns:
        A formatted string showing all counts with appropriate labels.

    Example:
        >>> counts = {
        ...     'directories': 10,
        ...     'files': 50,
        ...     'lines': 1000,
        ...     'characters': 50000,
        ...     'tokens': 8000
        ... }
        >>> print(format_counts(counts))
        Directories: 10
        Files: 50
        Lines: 1000
        Characters: 50000
        Tokens: 8000
    """
    return (
        f"Directories: {counts['directories']}\n"
        f"Files: {counts['files']}\n"
        f"Lines: {counts['lines']}\n"
        f"Characters: {counts['characters']}\n"
        f"Tokens: {counts['tokens'] if counts['tokens'] is not None else 'N/A (tokenizer not available)'}"
    )


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.

    Returns:
        An ArgumentParser instance configured with dir2text's options.
    """
    description = """
    dir2text: A utility for expressing directory contents in a format suitable for LLMs.

    This tool creates a comprehensive representation of a directory's structure and contents,
    designed specifically for use with Large Language Models (LLMs). It combines directory
    tree visualization with file contents in a format that preserves the relationship
    between files while being easy for LLMs to process.

    Key Features:
    - Generates tree-style directory structure visualization
    - Includes complete file contents with proper escaping
    - Supports exclusion patterns (e.g., .gitignore rules)
    - Optional token counting for LLM context management
    - Memory-efficient streaming processing
    - Multiple output formats (XML, JSON)

    The tool is particularly useful for:
    - Submitting codebases to LLMs for analysis
    - Documentation generation
    - Codebase visualization
    - Repository archiving in a human and machine-readable format

    Memory Usage:
    The tool processes files in a streaming fashion, maintaining constant memory usage
    regardless of the directory size. This makes it suitable for processing large
    directories without loading everything into memory.
    """

    epilog = """
    Examples:
      # Basic directory processing
      dir2text /path/to/project

      # Exclude files matching .gitignore patterns
      dir2text -e .gitignore /path/to/project

      # Count tokens for LLM context management
      dir2text -c /path/to/project

      # Generate JSON output and save to file
      dir2text --format json -o output.json /path/to/project

      # Process only specific aspects
      dir2text -T /path/to/project     # Skip tree visualization
      dir2text -C /path/to/project     # Skip file contents
    """

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "directory",
        type=Path,
        help="The directory to process. All paths in the output will be relative to this directory.",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        type=Path,
        metavar="FILE",
        help="Path to exclusion file (e.g., .gitignore) for filtering files and directories",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="Output file path. If not specified, output is written to stdout",
    )
    parser.add_argument(
        "-T",
        "--no-tree",
        action="store_true",
        help="Disable directory tree visualization in the output",
    )
    parser.add_argument(
        "-C",
        "--no-contents",
        action="store_true",
        help="Disable file content inclusion in the output",
    )
    parser.add_argument(
        "--format",
        choices=["xml", "json"],
        default="xml",
        help="Output format for file contents (default: xml)",
    )
    parser.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="Include counts of directories, files, lines, tokens, and characters",
    )
    parser.add_argument(
        "-t",
        "--tokenizer",
        default="gpt-4",
        help="Tokenizer model to use for counting tokens (default: gpt-4)",
    )

    return parser


def main() -> None:
    """Main entry point for the dir2text command-line interface.

    This function handles command-line argument parsing and orchestrates the
    directory analysis process. It manages output generation and error handling.

    Raises:
        Exception: Any exception that occurs during processing will be caught,
            logged to stderr, and result in an exit code of 1.

    Exit codes:
        0: Successful completion
        1: Runtime error during execution
        2: Command-line syntax error
        130: Interrupted by SIGINT (Ctrl+C)
        141: Broken pipe (SIGPIPE)
    """
    setup_signal_handling()

    try:
        parser = create_parser()
        try:
            args = parser.parse_args()
        except SystemExit:
            # argparse calls sys.exit(2) for argument errors
            raise

        # Initialize StreamingDir2Text with appropriate configuration
        analyzer = StreamingDir2Text(
            directory=args.directory,
            exclude_file=args.exclude,
            output_format=args.format,
            tokenizer_model=args.tokenizer if args.count else None,
        )

        output_file = args.output if args.output else sys.stdout.fileno()
        safe_writer = SafeWriter(output_file)

        try:
            if not args.no_tree:
                for line in analyzer.stream_tree():
                    safe_writer.write(line)

            if not args.no_contents:
                for chunk in analyzer.stream_contents():
                    safe_writer.write(chunk)

            if args.count:
                counts = {
                    "directories": analyzer.directory_count,
                    "files": analyzer.file_count,
                    "lines": analyzer.line_count,
                    "tokens": analyzer.token_count,
                    "characters": analyzer.character_count,
                }
                count_output_str = format_counts(counts)
                safe_writer.write("\n" + count_output_str + "\n")

            if args.no_tree and args.no_contents and not args.count:
                print(
                    "Warning: Both tree and contents printing were disabled, and counting was not enabled.",
                    end="",
                    file=sys.stderr,
                )
                print(" No output generated.", file=sys.stderr)

        except BrokenPipeError:
            pass  # We'll handle the exit in the finally block
        finally:
            safe_writer.close()

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # Handle exit codes based on received signals
    if signal_handler.sigpipe_received.is_set():
        sys.exit(141)
    elif signal_handler.sigint_received.is_set():
        sys.exit(130)


if __name__ == "__main__":
    main()
