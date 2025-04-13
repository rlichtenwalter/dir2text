"""Command-line interface for dir2text.

This module provides the command-line interface for dir2text, allowing users to generate
tree representations and file contents from directories. It handles command-line argument
parsing, output formatting, and signal management for graceful interruption handling.

Key Features:
    - Directory tree visualization
    - File content output in XML or JSON format
    - Token counting with model selection
    - Signal handling (SIGPIPE on Unix systems, SIGINT)
    - Exclusion rule support (e.g., .gitignore patterns)
    - Output redirection and file writing
    - Various output format options and combinations
    - Permission error handling
    - Version information display

Signal Handling Notes:
    The module implements careful signal handling to ensure proper cleanup on interruption:
    - SIGPIPE: Handled when output pipe is closed (e.g., when piping to `head`) on Unix-like systems
    - SIGINT: Handled for clean exit on Ctrl+C
    Both cases ensure proper cleanup and appropriate exit codes.

Exit Codes:
    0: Successful completion
    1: Runtime error during execution
    2: Command-line syntax error
    126: Permission denied
    130: Interrupted by SIGINT (Ctrl+C)
    141: Broken pipe (SIGPIPE) on Unix-like systems

Example:
    # Basic usage to process a directory
    $ dir2text /path/to/dir

    # With exclusions and permissive error handling
    $ dir2text /path/to/dir -e .gitignore -P warn

    # Display version information
    $ dir2text --version
"""

import importlib.util
import sys
from collections.abc import Mapping
from typing import Optional

from dir2text.cli.argparser import create_parser, validate_args
from dir2text.cli.safe_writer import SafeWriter
from dir2text.cli.signal_handler import setup_signal_handling, signal_handler
from dir2text.dir2text import StreamingDir2Text
from dir2text.exceptions import TokenizerNotAvailableError
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.file_system_tree.permission_action import PermissionAction


def format_counts(counts: Mapping[str, Optional[int]]) -> str:
    """Format the counts into a human-readable string.

    Args:
        counts: Mapping containing various count metrics.

    Returns:
        A formatted string showing all counts with appropriate labels.
    """
    result = [
        f"Directories: {counts['directories']}",
        f"Files: {counts['files']}",
        f"Symlinks: {counts['symlinks']}",
        f"Lines: {counts['lines']}",
        f"Characters: {counts['characters']}",
    ]

    if counts["tokens"] is not None:
        result.insert(4, f"Tokens: {counts['tokens']}")

    return "\n".join(result)


def check_tiktoken_available() -> bool:
    """Check if the tiktoken library is available.

    Returns:
        True if tiktoken is installed, False otherwise.
    """
    return importlib.util.find_spec("tiktoken") is not None


def main() -> None:
    """Main entry point for the dir2text command-line interface.

    This function handles command-line argument parsing and orchestrates the
    directory analysis process. It manages output generation and error handling.

    Exit codes:
        0: Successful completion
        1: Runtime error during execution
        2: Command-line syntax error
        126: Permission denied
        130: Interrupted by SIGINT (Ctrl+C)
        141: Broken pipe (SIGPIPE) on Unix-like systems
    """
    setup_signal_handling()

    try:
        # Create the exclusion rules object that will be populated during parsing
        exclusion_rules = GitIgnoreExclusionRules()

        # Create parser with the exclusion rules object
        parser = create_parser(exclusion_rules)
        try:
            args = parser.parse_args()
        except SystemExit:
            # argparse calls sys.exit(2) for argument errors
            # or sys.exit(0) for --version
            raise

        # Perform additional validation beyond what argparse supports directly
        validate_args(args)

        # Check if tokenizer is requested but tiktoken is not available
        if args.tokenizer and not check_tiktoken_available():
            raise TokenizerNotAvailableError(
                "Token counting was requested with -t/--tokenizer, but the required tiktoken library is not installed."
            )

        # Map CLI permission actions to internal enum
        perm_action = {
            "ignore": PermissionAction.IGNORE,
            "warn": PermissionAction.RAISE,
            "fail": PermissionAction.RAISE,
        }[args.permission_action]

        try:
            # Initialize StreamingDir2Text with appropriate configuration
            analyzer = StreamingDir2Text(
                directory=args.directory,
                exclusion_rules=exclusion_rules,
                output_format=args.format,
                tokenizer_model=args.tokenizer,
                permission_action=perm_action,
                follow_symlinks=args.follow_symlinks,
            )

            # Set up output
            output_file = args.output if args.output else sys.stdout.fileno()

            # Use SafeWriter as a context manager
            with SafeWriter(output_file) as safe_writer:
                try:
                    # Process tree if enabled
                    if not args.no_tree:
                        for line in analyzer.stream_tree():
                            safe_writer.write(line)

                    # Process contents if enabled
                    if not args.no_contents:
                        for chunk in analyzer.stream_contents():
                            safe_writer.write(chunk)

                    # Handle summary reporting based on the --summary argument
                    if args.summary:
                        counts = {
                            "directories": analyzer.directory_count,
                            "files": analyzer.file_count,
                            "symlinks": analyzer.symlink_count,
                            "lines": analyzer.line_count,
                            "tokens": analyzer.token_count,
                            "characters": analyzer.character_count,
                        }
                        count_output_str = format_counts(counts)

                        # Determine where to print the summary
                        if args.summary == "stdout":
                            # Print to stdout
                            safe_writer.write("\n" + count_output_str + "\n")
                        elif args.summary == "file":
                            # Include in the output file
                            safe_writer.write("\n" + count_output_str + "\n")
                        elif args.summary == "stderr":
                            # Print to stderr
                            print(count_output_str, file=sys.stderr)

                    # Check if nothing was actually output
                    if args.no_tree and args.no_contents and not args.summary:
                        print(
                            "Warning: Both tree and contents printing were disabled. No output generated.",
                            end="",
                            file=sys.stderr,
                        )

                except BrokenPipeError:
                    pass  # SafeWriter will automatically close in the context manager

        except PermissionError as e:
            if args.permission_action == "warn":
                print(f"Warning: {str(e)}", file=sys.stderr)
            elif args.permission_action == "fail":
                print(f"Error: {str(e)}", file=sys.stderr)
                sys.exit(126)
            # For "ignore", we simply continue

    except TokenizerNotAvailableError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        print("To enable token counting, install dir2text with the 'token_counting' extra:", file=sys.stderr)
        print('    pip install "dir2text[token_counting]"', file=sys.stderr)
        print("    # or with Poetry:", file=sys.stderr)
        print('    poetry add "dir2text[token_counting]"', file=sys.stderr)
        sys.exit(1)
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
