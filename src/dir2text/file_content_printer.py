from typing import Iterator, Optional, Tuple, Union

from .file_system_tree import FileSystemTree
from .output_strategies.base_strategy import OutputStrategy
from .output_strategies.json_strategy import JSONOutputStrategy
from .output_strategies.xml_strategy import XMLOutputStrategy
from .token_counter import TokenCounter


class FileContentPrinter:
    """
    Streams file content with consistent formatting while maintaining constant memory usage.

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
        tokenizer (Optional[TokenCounter]): Optional token counter for content analysis.
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
        """
        Initialize the FileContentPrinter.

        Args:
            fs_tree (FileSystemTree): The filesystem tree to process.
            output_format (Union[str, OutputStrategy], optional): Either a string specifying
                the format ("xml" or "json") or an OutputStrategy instance. Defaults to "xml".
            tokenizer (Optional[TokenCounter], optional): Token counter for content analysis.
                Defaults to None.

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
        """
        Stream file content with metadata and formatting.

        This method implements the core streaming functionality of the printer. It yields
        tuples containing file paths and a content iterator for each file. The content
        iterator itself yields chunks of formatted content, ensuring that only a small
        portion of any file needs to be in memory at once.

        The streaming process works as follows:
        1. Files are yielded one at a time from the filesystem tree
        2. For each file, content is read and processed in chunks
        3. Each chunk is formatted and yielded immediately
        4. Memory usage remains constant regardless of file size

        Yields:
            Iterator[Tuple[str, str, Iterator[str]]]: Tuples of (absolute_path,
                relative_path, content_iterator) where content_iterator yields formatted
                chunks of the file's content.

        Example:
            >>> from dir2text.file_system_tree import FileSystemTree
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> printer = FileContentPrinter(tree, "xml")  # doctest: +SKIP
            >>> # In practice, you would process files like this:
            >>> for abs_path, rel_path, content_iter in printer.yield_file_contents():  # doctest: +SKIP
            ...     print(f"Processing {rel_path}")
            ...     for chunk in content_iter:
            ...         # Process each chunk as it becomes available
            ...         print(chunk, end="")
        """
        for file_path, relative_path in self.fs_tree.iterate_files():
            yield file_path, relative_path, self._yield_wrapped_content(file_path, relative_path)

    def _yield_wrapped_content(self, file_path: str, relative_path: str) -> Iterator[str]:
        """Stream a single file's content with appropriate formatting.

        Implements chunk-based streaming for a single file, including format-specific
        wrappers and optional token counting. The streaming process ensures constant
        memory usage regardless of file size through:
        - Reading file content in fixed-size chunks
        - Processing and yielding each chunk immediately
        - Maintaining only one chunk in memory at a time

        Token counting behavior depends on the output strategy's requirements:
        - If tokens must be in the start tag: Pre-counts tokens with an initial pass
        - If tokens can be in the end tag: Counts tokens during content streaming

        Args:
            file_path (str): Absolute path to the file.
            relative_path (str): Path relative to the root directory.

        Yields:
            str: Chunks of formatted file content, including wrapping elements.
        """
        file_token_count = None
        if self.tokenizer:
            if self.output_strategy.requires_tokens_in_start:
                # Pre-count tokens for strategies requiring token count in start tag
                file_token_count = sum(
                    token_count for _, token_count in self._process_file_content(file_path, count=True)
                )

        # Output start tag (with token count if required upfront)
        yield self.output_strategy.format_start(relative_path, file_token_count)

        # Stream and optionally count content
        running_token_count = 0
        for chunk, token_count in self._process_file_content(
            file_path, count=self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start
        ):
            yield self.output_strategy.format_content(chunk)
            if self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start:
                running_token_count += token_count

        # Output end tag with token count only if not required in start
        if self.tokenizer is not None and not self.output_strategy.requires_tokens_in_start:
            file_token_count = running_token_count

        yield self.output_strategy.format_end(
            None if self.output_strategy.requires_tokens_in_start else file_token_count
        )

    def _process_file_content(self, file_path: str, count: bool = False) -> Iterator[Tuple[str, int]]:
        """
        Stream file content in chunks with optional token counting.

        Implements the lowest level of the streaming process, reading file content
        in fixed-size chunks to maintain constant memory usage regardless of file size.

        Args:
            file_path (str): Path to the file to process.
            count (bool, optional): Whether to count tokens in the content.
                Defaults to False.

        Yields:
            Tuple[str, int]: Pairs of (content_chunk, token_count). If count is False,
                token_count will always be 0.

        Note:
            Uses a 64KB chunk size to balance memory usage and performance.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                while True:
                    chunk = file.read(65536)  # Read in 64KB chunks
                    if not chunk:
                        break

                    token_count = self.tokenizer.count_tokens(chunk) if self.tokenizer and count else 0
                    yield chunk, token_count

        except Exception as e:
            error_message = f"Error reading file {file_path}: {str(e)}\n"
            yield error_message, 0  # Error messages are not counted

    def get_output_file_extension(self) -> str:
        """
        Get the appropriate file extension for the current output format.

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
