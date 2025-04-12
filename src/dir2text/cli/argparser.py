"""Command-line argument parsing for dir2text.

This module defines the command-line interface for dir2text,
handling argument parsing and validation.
"""

import argparse
import os
from pathlib import Path
from typing import Any, List, Optional, Sequence, Type, Union

from dir2text import __version__
from dir2text.exclusion_rules.base_rules import BaseExclusionRules


def create_exclusion_action(exclusion_rules: BaseExclusionRules) -> Type[argparse.Action]:
    """Create a custom action class for handling exclusion rules.

    This factory function creates an action class that will update the provided
    exclusion rules object as arguments are processed. This preserves the exact
    order of exclusion specifications as they appear on the command line.

    Args:
        exclusion_rules: The exclusion rules object to update during parsing.

    Returns:
        A custom action class for use with argparse.
    """

    class ExclusionRulesAction(argparse.Action):
        """Action to update exclusion rules as arguments are processed.

        This action adds rules to the provided exclusion rules object as they are
        encountered during argument parsing, preserving their order on the command line.
        """

        def __init__(self, option_strings: List[str], dest: str, **kwargs: Any) -> None:
            super().__init__(option_strings, dest, **kwargs)

        def __call__(
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: Union[str, Sequence[Any], None],
            option_string: Optional[str] = None,
        ) -> None:
            # Process based on the option type
            if option_string in ("-e", "--exclude"):
                # It's a file-based exclusion
                if values is not None:
                    if isinstance(values, (str, os.PathLike)):
                        exclusion_rules.load_rules(values)
                    else:
                        # For unexpected types, try to convert or handle appropriately
                        exclusion_rules.load_rules(Path(str(values)))
            else:  # -i/--ignore
                # It's a pattern-based exclusion
                if values is not None:
                    # add_rule expects a string
                    exclusion_rules.add_rule(str(values))

            # Also maintain the original attributes for backward compatibility
            if option_string in ("-e", "--exclude"):
                if not hasattr(namespace, "exclude") or namespace.exclude is None:
                    namespace.exclude = []
                namespace.exclude.append(values)
            else:  # -i/--ignore
                if not hasattr(namespace, "ignore") or namespace.ignore is None:
                    namespace.ignore = []
                namespace.ignore.append(values)

    return ExclusionRulesAction


def create_parser(exclusion_rules: BaseExclusionRules) -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.

    Args:
        exclusion_rules: The exclusion rules object to update during parsing.

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
    - Configurable permission error handling

    Memory Usage:
    The tool processes files in a streaming fashion, maintaining constant memory usage
    regardless of the directory size. This makes it suitable for processing large
    directories without loading everything into memory.
    """

    epilog = """
    Examples:
      # Basic directory processing
      dir2text /path/to/project

      # Follow symbolic links (dereference symlinks)
      dir2text -L /path/to/project

      # Exclude files matching patterns from one or more exclusion files
      dir2text -e .gitignore /path/to/project
      dir2text -e .gitignore -e .npmignore -e custom-ignore /path/to/project

      # Exclude files directly using gitignore-style patterns
      dir2text -i "*.pyc" -i "node_modules/" /path/to/project

      # Mix file-based and direct pattern exclusions
      dir2text -e .gitignore -i "*.log" -i "!important.log" /path/to/project

      # Enable token counting for LLM context management
      dir2text -t gpt-4 /path/to/project

      # Generate JSON output and save to file
      dir2text --format json -o output.json /path/to/project

      # Process with different permission handling
      dir2text -P warn /path/to/project    # Continue with warnings
      dir2text -P fail /path/to/project    # Stop on permission errors
      dir2text -P ignore /path/to/project  # Skip silently (default)

      # Process only specific aspects
      dir2text -T /path/to/project     # Skip tree visualization
      dir2text -C /path/to/project     # Skip file contents

      # Print summary to stderr
      dir2text -s stderr /path/to/project

      # Print summary to stdout
      dir2text -s stdout /path/to/project

      # Include summary in the output file
      dir2text -s file -o output.txt /path/to/project

      # Display version information and exit
      dir2text -V
      dir2text --version
    """

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Version information
    parser.add_argument(
        "-V", "--version", action="version", version=f"dir2text {__version__}", help="Show the version and exit"
    )

    # Create the exclusion rules action class
    ExclusionAction = create_exclusion_action(exclusion_rules)

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
        action=ExclusionAction,
        help=(
            "Path to exclusion file (e.g., .gitignore) for filtering files and directories "
            "(can be specified multiple times)."
        ),
    )
    parser.add_argument(
        "-i",
        "--ignore",
        type=str,
        metavar="PATTERN",
        action=ExclusionAction,
        help=(
            "Individual gitignore-style pattern to exclude files and directories. Can be any valid "
            "gitignore pattern including wildcards (*.txt), directory markers (build/), negations "
            "(!important.txt), etc. Can be specified multiple times, and patterns are processed in "
            "the order they appear, mixed with -e/--exclude options."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="Output file path. If not specified, output is written to stdout.",
    )
    parser.add_argument(
        "-T",
        "--no-tree",
        action="store_true",
        help="Disable directory tree visualization in the output.",
    )
    parser.add_argument(
        "-C",
        "--no-contents",
        action="store_true",
        help="Disable file content inclusion in the output.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["xml", "json"],
        default="xml",
        help="Output format for file contents (default: xml).",
    )
    parser.add_argument(
        "-L",
        "--follow-symlinks",
        action="store_true",
        help=(
            "Follow symbolic links during traversal. By default, symlinks are represented as symlinks "
            "without following."
        ),
    )
    parser.add_argument(
        "-s",
        "--summary",
        metavar="DEST",
        choices=["stderr", "stdout", "file"],
        help="Print summary report. Valid destinations: stderr, stdout, file (requires -o)",
    )
    parser.add_argument(
        "-t",
        "--tokenizer",
        metavar="MODEL",
        help="Tokenizer model to use for counting tokens (e.g., gpt-4). Specifying this enables token counting.",
    )
    parser.add_argument(
        "-P",
        "--permission-action",
        choices=["ignore", "warn", "fail"],
        default="ignore",
        help="How to handle permission errors (default: ignore).",
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments.

    Performs additional validation beyond what argparse can handle.

    Args:
        args: Parsed command-line arguments.

    Raises:
        ValueError: If any arguments fail validation.
    """
    # Validate that if summary=file is specified, -o must also be provided
    if args.summary == "file" and not args.output:
        raise ValueError("--summary=file requires -o/--output to be specified")
