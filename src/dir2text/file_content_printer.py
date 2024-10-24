"""File content printer with streaming support.

This module implements streaming content processing with proper formatting
and optional content counting. It provides configurable encoding support
for reading files while maintaining memory-efficient streaming behavior.
"""

from typing import Iterator, Optional, Tuple, Union

from .file_system_tree import FileSystemTree
from .io.chunked_file_reader import ChunkedFileReader
from .output_strategies.base_strategy import OutputStrategy
from .output_strategies.json_strategy import JSONOutputStrategy
from .output_strategies.xml_strategy import XMLOutputStrategy
from .token_counter import TokenCounter


class FileContentPrinter:
    """Streams file content with consistent formatting while maintaining constant memory usage.

    This class coordinates between the filesystem tree and output formatting strategies to
    produce formatted file content. Its architecture is fundamentally stream-based - files
    are processed in chunks and passed through the formatting pipeline without requiring
    the entire file content to be held in memory. This design enables processing of files
    of arbitrary size while maintaining constant memory usage.

    The streaming design is achieved through:
    - Yielding individual file paths rather than collecting them
    - Processing file content in fixed-size chunks using ChunkedFileReader
    - Streaming formatted output piece by piece
    - Maintaining constant memory usage regardless of file sizes

    Files are read using the specified encoding (UTF-8 by default) with configurable
    error handling for decode errors.

    Attributes:
        fs_tree (FileSystemTree): The filesystem tree to process.
        tokenizer (Optional[TokenCounter]): Optional counter for content analysis.
        output_strategy (OutputStrategy): Strategy for formatting the output.
        encoding (str): The encoding to use when reading files.
        errors (str): How to handle encoding errors when reading files.

    Example:
        >>> from dir2text.file_system_tree import FileSystemTree
        >>> tree = FileSystemTree("src")  # doctest: +SKIP
        >>> printer = FileContentPrinter(tree)  # doctest: +SKIP
        >>> for path, rel_path, content in printer.yield_file_contents():  # doctest: +SKIP
        ...     for chunk in content:
        ...         print(chunk, end='')  # Process chunks as they arrive
    """

    def __init__(
        self,
        fs_tree: FileSystemTree,
        output_format: Union[str, OutputStrategy] = "xml",
        tokenizer: Optional[TokenCounter] = None,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> None:
        """Initialize the FileContentPrinter.

        Args:
            fs_tree: The filesystem tree to process.
            output_format: Either a string specifying the format ("xml" or "json")
                or an OutputStrategy instance. Defaults to "xml".
            tokenizer: Optional counter for content analysis. Defaults to None.
            encoding: The encoding to use when reading files. Defaults to "utf-8".
            errors: How to handle encoding errors. Must be one of "strict" (raises error),
                "ignore" (skips invalid bytes), or "replace" (replaces invalid bytes with
                a replacement marker). Defaults to "strict".

        Raises:
            ValueError: If output_format string is not "xml" or "json", or if errors
                is not one of "strict", "ignore", or "replace".
            TypeError: If output_format is neither a string nor an OutputStrategy.
            LookupError: If the specified encoding is not available.
            UnicodeError: If the encoding validation test fails.
            TokenizationError: If token counting is enabled but the tokenizer fails to initialize.
        """
        # Validate errors parameter
        if errors not in ("strict", "ignore", "replace"):
            raise ValueError(f"Invalid error handler '{errors}'. Must be one of: strict, ignore, replace")

        # Validate encoding early to fail fast
        try:
            "test".encode(encoding).decode(encoding)
        except LookupError as e:
            raise LookupError(f"Encoding '{encoding}' is not available") from e
        except UnicodeError as e:
            raise UnicodeError(f"Encoding '{encoding}' validation failed: {str(e)}") from e

        self.fs_tree = fs_tree
        self.tokenizer = tokenizer
        self.encoding = encoding
        self.errors = errors

        # Set up output strategy
        if isinstance(output_format, str):
            output_format = output_format.lower()
            if output_format == "xml":
                self.output_strategy: OutputStrategy = XMLOutputStrategy()
            elif output_format == "json":
                self.output_strategy = JSONOutputStrategy()
            else:
                raise ValueError(f"Unsupported output format: {output_format}. Must be one of: xml, json")
        elif isinstance(output_format, OutputStrategy):
            self.output_strategy = output_format
        else:
            raise TypeError("output_format must be either a string ('xml' or 'json') or " "an OutputStrategy instance")

    def _count_file_tokens(self, file_path: str, relative_path: str) -> int:
        """Count tokens in a file without storing its content.

        Args:
            file_path: Absolute path to the file.
            relative_path: Path relative to the root directory.

        Returns:
            int: Total number of tokens in the file.

        Raises:
            OSError: If there are errors reading the file.
            ValueError: If a file cannot be decoded using the specified encoding.
            LookupError: If the specified encoding is not available.
        """
        if self.tokenizer is None:
            return 0

        token_count = 0
        try:
            with open(file_path, "r", encoding=self.encoding, errors=self.errors) as file:
                reader = ChunkedFileReader(file)
                for chunk in reader:
                    token_count += self.tokenizer.count(self.output_strategy.format_content(chunk)).tokens
        except UnicodeError as e:
            raise ValueError(
                f"Failed to decode '{relative_path}' with {self.encoding} "
                f"encoding (errors='{self.errors}'): {str(e)}"
            ) from e
        except OSError as e:
            raise OSError(f"Failed to read '{relative_path}': {str(e)}") from e

        return token_count

    def _yield_wrapped_content(self, file_path: str, relative_path: str) -> Iterator[str]:
        """Stream a single file's content with appropriate formatting.

        Args:
            file_path: Absolute path to the file.
            relative_path: Path relative to the root directory.

        Yields:
            str: Chunks of formatted file content.

        Raises:
            OSError: If there are errors reading the file.
            ValueError: If a file cannot be decoded using the specified encoding or
                if the 'errors' parameter is invalid.
            LookupError: If the specified encoding is not available.
        """
        token_count = None
        if self.tokenizer is not None and self.output_strategy.requires_tokens_in_start:
            token_count = self._count_file_tokens(file_path, relative_path)

        # Output start tag with token count if available
        yield self.output_strategy.format_start(relative_path, token_count)

        if self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start:
            token_count = 0

        try:
            with open(file_path, "r", encoding=self.encoding, errors=self.errors) as file:
                reader = ChunkedFileReader(file)
                for chunk in reader:
                    formatted_chunk = self.output_strategy.format_content(chunk)
                    # Only count tokens during processing if we haven't counted them upfront
                    if self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start:
                        token_count += self.tokenizer.count(formatted_chunk).tokens
                    yield formatted_chunk

        except ValueError as e:
            # Handle invalid 'errors' parameter - this comes from open()
            if "errors" in str(e):
                raise ValueError(
                    f"Invalid error handler '{self.errors}' for '{relative_path}'. "
                    "Must be one of: strict, ignore, replace"
                ) from e
            raise

        except OSError as e:
            # Add context to OS-level errors
            raise OSError(f"Failed to read '{relative_path}': {str(e)}") from e

        # Output end tag
        if self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start:
            yield self.output_strategy.format_end(token_count)
        else:
            yield self.output_strategy.format_end()

    def yield_file_contents(self) -> Iterator[Tuple[str, str, Iterator[str]]]:
        """Stream file content with metadata and formatting.

        This method implements the core streaming functionality of the printer. It yields
        tuples containing file paths and a content iterator for each file. The content
        iterator itself yields chunks of formatted content, ensuring that only a small
        portion of any file needs to be in memory at once.

        Yields:
            Iterator[Tuple[str, str, Iterator[str]]]: Tuples of (absolute_path,
                relative_path, content_iterator) where content_iterator yields formatted
                chunks of the file's content.

        Raises:
            OSError: If there are errors reading files or accessing the filesystem.
            UnicodeError: If a file cannot be decoded using the specified encoding.
            LookupError: If the specified encoding is not available.
            ValueError: If the 'errors' parameter is invalid or if there's an
                encoding configuration error.
        """
        try:
            for file_path, relative_path in self.fs_tree.iterate_files():
                yield file_path, relative_path, self._yield_wrapped_content(file_path, relative_path)
        except OSError as e:
            # Add context to filesystem iteration errors
            raise OSError(f"Failed to iterate directory structure: {str(e)}") from e

    def get_output_file_extension(self) -> str:
        """Get the appropriate file extension for the current output format.

        Returns:
            str: The file extension (including the dot) for the current output format.

        Example:
            >>> from dir2text.file_system_tree import FileSystemTree
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> printer = FileContentPrinter(tree, "xml")  # doctest: +SKIP
            >>> printer.get_output_file_extension()  # doctest: +SKIP
            '.xml'
        """
        return self.output_strategy.get_file_extension()
