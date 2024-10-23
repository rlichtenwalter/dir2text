"""File content printer with streaming support.

This module implements streaming content processing with proper formatting
and optional content counting.
"""

from typing import Iterator, Optional, Tuple, Union

from .file_system_tree import FileSystemTree
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
    - Processing file content in fixed-size chunks
    - Streaming formatted output piece by piece
    - Maintaining constant memory usage regardless of file sizes

    Attributes:
        fs_tree (FileSystemTree): The filesystem tree to process.
        tokenizer (Optional[TokenCounter]): Optional counter for content analysis.
        output_strategy (OutputStrategy): Strategy for formatting the output.

    Example:
        >>> from dir2text.file_system_tree import FileSystemTree
        >>> # We'll skip actual filesystem operations in this example
        >>> import sys
        >>> tree = FileSystemTree("src")  # doctest: +SKIP
        >>> printer = FileContentPrinter(tree, "xml")  # doctest: +SKIP
        >>> for path, rel_path, content in printer.yield_file_contents():  # doctest: +SKIP
        ...     for chunk in content:
        ...         sys.stdout.write(chunk)  # Process chunks as they arrive
    """

    def __init__(
        self,
        fs_tree: FileSystemTree,
        output_format: Union[str, OutputStrategy] = "xml",
        tokenizer: Optional[TokenCounter] = None,
    ):
        """Initialize the FileContentPrinter.

        Args:
            fs_tree: The filesystem tree to process.
            output_format: Either a string specifying the format ("xml" or "json")
                or an OutputStrategy instance. Defaults to "xml".
            tokenizer: Optional counter for content analysis. Defaults to None.

        Raises:
            ValueError: If output_format string is not "xml" or "json".
            TypeError: If output_format is neither a string nor an OutputStrategy.

        Example:
            >>> from dir2text.file_system_tree import FileSystemTree
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> # With string format
            >>> printer = FileContentPrinter(tree, "json")  # doctest: +SKIP
            >>> # With strategy instance
            >>> from dir2text.output_strategies.json_strategy import JSONOutputStrategy
            >>> strategy = JSONOutputStrategy()
            >>> printer = FileContentPrinter(tree, strategy)  # doctest: +SKIP
        """
        self.fs_tree = fs_tree
        self.tokenizer = tokenizer

        if isinstance(output_format, str):
            output_format = output_format.lower()
            if output_format == "xml":
                self.output_strategy: OutputStrategy = XMLOutputStrategy()
            elif output_format == "json":
                self.output_strategy = JSONOutputStrategy()
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
        elif isinstance(output_format, OutputStrategy):
            self.output_strategy = output_format
        else:
            raise TypeError("output_format must be either a string or an OutputStrategy instance")

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

        Example:
            >>> from dir2text.file_system_tree import FileSystemTree
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> printer = FileContentPrinter(tree, "xml")  # doctest: +SKIP
            >>> # Process files as they become available:
            >>> for abs_path, rel_path, content_iter in printer.yield_file_contents():  # doctest: +SKIP
            ...     print(f"Processing {rel_path}")
            ...     for chunk in content_iter:
            ...         print(chunk, end="")
        """
        for file_path, relative_path in self.fs_tree.iterate_files():
            yield file_path, relative_path, self._yield_wrapped_content(file_path, relative_path)

    def _yield_wrapped_content(self, file_path: str, relative_path: str) -> Iterator[str]:
        """Stream a single file's content with appropriate formatting.

        Args:
            file_path: Absolute path to the file.
            relative_path: Path relative to the root directory.

        Yields:
            str: Chunks of formatted file content.

        Raises:
            OSError: If there are errors reading the file.
        """
        # Output start tag
        yield self.output_strategy.format_start(relative_path)

        # Stream content
        with open(file_path, "r", encoding="utf-8") as file:
            while True:
                chunk = file.read(65536)  # Read in 64KB chunks
                if not chunk:
                    break
                yield self.output_strategy.format_content(chunk)

        # Output end tag
        yield self.output_strategy.format_end()

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
