"""File content printer with streaming support.

This module implements streaming content processing with proper formatting
and optional content counting. It provides configurable encoding support
for reading files while maintaining memory-efficient streaming behavior.
"""

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Tuple, Union

from .exceptions import BinaryFileError
from .file_system_tree.binary_action import BinaryAction
from .file_system_tree.binary_detector import is_binary_file
from .file_system_tree.file_system_tree import FileSystemTree
from .io.chunked_file_reader import ChunkedFileReader
from .output_strategies.base_strategy import OutputStrategy
from .output_strategies.json_strategy import JSONOutputStrategy
from .output_strategies.xml_strategy import XMLOutputStrategy
from .token_counter import TokenCounter
from .types import PathType


@dataclass(frozen=True)
class FileInfo:
    """Metadata about a file including binary detection results.

    This class carries file information and binary detection results to avoid
    redundant detection operations during file processing.

    Attributes:
        path: Absolute path to the file.
        relative_path: Relative path for display purposes.
        is_binary: True if file is binary, False if text, None if not yet determined.
        detection_error: OSError encountered during binary detection, if any.
    """

    path: Path
    relative_path: str
    is_binary: Optional[bool] = None
    detection_error: Optional[OSError] = None


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
        >>> from dir2text.file_system_tree.file_system_tree import FileSystemTree
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
        binary_action: BinaryAction = BinaryAction.IGNORE,
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
            binary_action: How to handle binary files. Must be one of BinaryAction values.
                Defaults to IGNORE.

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
        self.binary_action = binary_action

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

    def _create_file_info(self, file_path: str, relative_path: str) -> FileInfo:
        """Create FileInfo with binary detection results.

        This method performs binary detection once and caches the result,
        eliminating the need for redundant detection operations.

        Args:
            file_path: Absolute path to the file.
            relative_path: Relative path for display purposes.

        Returns:
            FileInfo: Object containing file metadata and binary detection results.
        """
        path_obj = Path(file_path)
        is_binary = None
        detection_error = None

        try:
            is_binary = is_binary_file(path_obj)
        except OSError as e:
            # Consistent error handling: treat as text file when detection fails
            is_binary = False
            detection_error = e

        return FileInfo(
            path=path_obj, relative_path=relative_path, is_binary=is_binary, detection_error=detection_error
        )

    def _count_file_tokens(self, file_path: PathType, relative_path: str) -> Optional[int]:
        """Count tokens in a file without storing its content.

        Args:
            file_path: Absolute path to the file. Can be any path-like object.
            relative_path: Path relative to the root directory.

        Returns:
            Optional[int]: Total number of tokens in the file, or None if tokenizer is not available or
                 doesn't have token counting capabilities.

        Raises:
            OSError: If there are errors reading the file.
            ValueError: If a file cannot be decoded using the specified encoding.
            LookupError: If the specified encoding is not available.
        """
        # Only attempt token counting if a tokenizer is available with token counting capabilities
        if self.tokenizer is None or self.tokenizer.get_total_tokens() is None:
            return None

        token_count = 0
        path_obj = Path(file_path)
        try:
            with open(path_obj, "r", encoding=self.encoding, errors=self.errors) as file:
                reader = ChunkedFileReader(file)
                for chunk in reader:
                    result = self.tokenizer.count(self.output_strategy.format_content(chunk))
                    if result.tokens is not None:
                        token_count += result.tokens
        except UnicodeError as e:
            raise ValueError(
                f"Failed to decode '{relative_path}' with {self.encoding} "
                f"encoding (errors='{self.errors}'): {str(e)}"
            ) from e
        except OSError as e:
            raise OSError(f"Failed to read '{relative_path}': {str(e)}") from e

        return token_count

    def _count_binary_file_tokens(self, file_path: PathType, relative_path: str) -> Optional[int]:
        """Pre-count tokens in a binary file's base64 content for start tag display.

        This method is only used when the output strategy requires tokens in the start tag,
        necessitating a full file read before streaming. It mirrors _count_file_tokens
        for text files.

        Args:
            file_path: Absolute path to the binary file.
            relative_path: Path relative to the root directory (for error messages).

        Returns:
            Optional[int]: Total token count for base64 content, or None if unavailable.
        """
        if self.tokenizer is None:
            return None

        try:
            total_tokens = 0
            chunk_size = 65535  # Same base64-aligned chunk size as streaming

            with open(file_path, "rb") as file:
                while True:
                    binary_chunk = file.read(chunk_size)
                    if not binary_chunk:
                        break

                    # Convert to base64 and count tokens (same as streaming path)
                    b64_chunk = base64.b64encode(binary_chunk).decode("ascii")
                    formatted_chunk = self.output_strategy.format_content(b64_chunk)

                    result = self.tokenizer.count(formatted_chunk)
                    if result.tokens is not None:
                        total_tokens += result.tokens

            return total_tokens

        except OSError as e:
            raise OSError(f"Failed to count tokens in binary file '{relative_path}': {str(e)}") from e

    def _yield_wrapped_binary_content(self, file_path: PathType, relative_path: str) -> Iterator[str]:
        """Stream a binary file's content as base64-encoded chunks.

        Args:
            file_path: Absolute path to the file. Can be any path-like object.
            relative_path: Path relative to the root directory.

        Yields:
            str: Chunks of base64-encoded file content with appropriate formatting.

        Raises:
            OSError: If there are errors reading the file.
        """
        path_obj = Path(file_path)

        # For binary files, we count tokens for the base64-encoded content
        # This ensures consistent token counting behavior across all file types
        token_count = None

        # Calculate token count for base64 content if required in start tag
        # This mirrors the same pattern used for text files
        if (
            self.tokenizer is not None
            and self.tokenizer.get_total_tokens() is not None
            and self.output_strategy.requires_tokens_in_start
        ):
            # Pre-count tokens for start tag (requires full file read)
            token_count = self._count_binary_file_tokens(path_obj, relative_path)

        yield self.output_strategy.format_start(relative_path + " [binary]", "binary", token_count)

        # Initialize streaming token counting if not requiring tokens in start
        if self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start:
            token_count = 0

        try:
            # Use base64-aligned chunk size for cleaner intermediate encoding
            # 65535 = 21845 * 3, ensuring each chunk (except possibly the last)
            # encodes without padding. While base64 processes each chunk as a unit
            # regardless of alignment, this eliminates unnecessary padding in
            # intermediate chunks, following base64 streaming best practices.
            chunk_size = 65535
            with open(path_obj, "rb") as file:
                while True:
                    binary_chunk = file.read(chunk_size)
                    if not binary_chunk:
                        break

                    # Encode to base64 and format as content
                    b64_chunk = base64.b64encode(binary_chunk).decode("ascii")
                    formatted_chunk = self.output_strategy.format_content(b64_chunk)

                    # Count tokens in streaming mode (mirrors text file behavior)
                    if self.tokenizer is not None:
                        result = self.tokenizer.count(formatted_chunk)
                        # Only accumulate tokens if we're tracking them and not requiring them in start
                        if result.tokens is not None and not self.output_strategy.requires_tokens_in_start:
                            token_count += result.tokens

                    yield formatted_chunk

        except OSError as e:
            # Add context to OS-level errors
            raise OSError(f"Failed to read binary file '{relative_path}': {str(e)}") from e

        # Output end tag with token count if available (mirrors text file behavior)
        if (
            self.tokenizer is not None
            and self.tokenizer.get_total_tokens() is not None
            and not self.output_strategy.requires_tokens_in_start
        ):
            yield self.output_strategy.format_end(token_count)
        else:
            yield self.output_strategy.format_end()

    def _yield_wrapped_content(self, file_path: PathType, relative_path: str) -> Iterator[str]:
        """Stream a single file's content with appropriate formatting.

        This method now serves as a compatibility wrapper around the optimized
        _yield_wrapped_content_with_info method to eliminate code duplication.

        Args:
            file_path: Absolute path to the file. Can be any path-like object.
            relative_path: Path relative to the root directory.

        Yields:
            str: Chunks of formatted file content.

        Raises:
            OSError: If there are errors reading the file.
            ValueError: If a file cannot be decoded using the specified encoding or
                if the 'errors' parameter is invalid.
            LookupError: If the specified encoding is not available.
            BinaryFileError: If a binary file is encountered and binary_action is RAISE.
        """
        # Create FileInfo and delegate to the optimized method
        file_info = self._create_file_info(str(file_path), relative_path)
        yield from self._yield_wrapped_content_with_info(file_info)

    def _yield_wrapped_content_with_info(self, file_info: FileInfo) -> Iterator[str]:
        """Stream a single file's content using pre-computed binary detection results.

        This method eliminates redundant binary detection by using results from FileInfo.
        It provides the same functionality as _yield_wrapped_content but with better
        performance and consistent error handling.

        Args:
            file_info: FileInfo containing file metadata and binary detection results.

        Yields:
            str: Chunks of formatted file content.

        Raises:
            OSError: If there are errors reading the file.
            ValueError: If a file cannot be decoded using the specified encoding.
            BinaryFileError: If a binary file is encountered and binary_action is RAISE.
        """
        # Use pre-computed binary detection results
        if file_info.is_binary:
            if self.binary_action == BinaryAction.RAISE:
                # Raise an exception that will be caught at the CLI level
                raise BinaryFileError(str(file_info.path))
            elif self.binary_action == BinaryAction.ENCODE:
                # Use the binary content handler
                yield from self._yield_wrapped_binary_content(str(file_info.path), file_info.relative_path)
                return

        # Proceed with text file handling
        token_count = None

        # Only count tokens if the tokenizer has token counting capabilities
        if (
            self.tokenizer is not None
            and self.tokenizer.get_total_tokens() is not None
            and self.output_strategy.requires_tokens_in_start
        ):
            token_count = self._count_file_tokens(file_info.path, file_info.relative_path)

        # Output start tag with token count if available
        yield self.output_strategy.format_start(file_info.relative_path, "text", token_count)

        if self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start:
            token_count = 0

        try:
            with open(file_info.path, "r", encoding=self.encoding, errors=self.errors) as file:
                reader = ChunkedFileReader(file)
                for chunk in reader:
                    formatted_chunk = self.output_strategy.format_content(chunk)

                    # Count lines and characters (and potentially tokens)
                    if self.tokenizer is not None:
                        result = self.tokenizer.count(formatted_chunk)
                        # Only accumulate tokens if we're tracking them and not requiring them in start
                        if result.tokens is not None and not self.output_strategy.requires_tokens_in_start:
                            token_count += result.tokens

                    yield formatted_chunk

        except OSError as e:
            # Add context to OS-level errors
            raise OSError(f"Failed to read '{file_info.relative_path}': {str(e)}") from e

        # Output end tag
        if (
            self.tokenizer is not None
            and self.tokenizer.get_total_tokens() is not None
            and not self.output_strategy.requires_tokens_in_start
        ):
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
            # Process regular files
            for file_path, relative_path in self.fs_tree.iterate_files():
                # Create FileInfo with single binary detection
                file_info = self._create_file_info(file_path, relative_path)

                # Apply binary action filtering
                if file_info.is_binary and self.binary_action == BinaryAction.IGNORE:
                    continue  # Skip binary files when action is IGNORE

                # Yield file with pre-computed binary detection results
                yield file_path, relative_path, self._yield_wrapped_content_with_info(file_info)

            # Process symlinks if the tree is not following them
            if not self.fs_tree.follow_symlinks:
                for abs_path, rel_path, target in self.fs_tree.iterate_symlinks():
                    # For symlinks, we yield a single formatted string instead of a content iterator
                    symlink_str = self.output_strategy.format_symlink(rel_path, target)

                    # Create a single-item iterator to maintain the same interface as file content
                    def symlink_iterator() -> Iterator[str]:
                        yield symlink_str

                    yield abs_path, rel_path, symlink_iterator()

        except OSError as e:
            # Add context to filesystem iteration errors
            raise OSError(f"Failed to iterate directory structure: {str(e)}") from e

    def get_output_file_extension(self) -> str:
        """Get the appropriate file extension for the current output format.

        Returns:
            str: The file extension (including the dot) for the current output format.

        Example:
            >>> from dir2text.file_system_tree.file_system_tree import FileSystemTree
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> printer = FileContentPrinter(tree, "xml")  # doctest: +SKIP
            >>> printer.get_output_file_extension()  # doctest: +SKIP
            '.xml'
        """
        return self.output_strategy.get_file_extension()
