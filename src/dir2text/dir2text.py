"""Directory to text conversion with streaming support.

This module provides classes for converting directory structures to text format,
with support for streaming output and token counting. It includes both streaming
and complete processing implementations.
"""

from pathlib import Path
from typing import Iterator, Optional, Union

from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.file_content_printer import FileContentPrinter
from dir2text.file_system_tree import FileSystemTree
from dir2text.output_strategies.base_strategy import OutputStrategy
from dir2text.output_strategies.json_strategy import JSONOutputStrategy
from dir2text.output_strategies.xml_strategy import XMLOutputStrategy
from dir2text.token_counter import TokenCounter


class StreamingDir2Text:
    """Streaming directory analyzer that minimizes memory usage through incremental processing.

    This class provides a memory-efficient interface for analyzing directory structures and
    their contents. It processes files incrementally, reading and outputting content in
    chunks rather than loading entire files into memory. This streaming approach enables
    processing of large directories and files while maintaining constant memory usage.

    Streaming properties:
    - Each streaming operation (tree, contents) can only be performed once
    - Metrics are updated incrementally as content is processed
    - Metrics reflect only processed content until streaming_complete is True
    - Each type of content (tree, file contents) must be either fully streamed or not at all

    Attributes:
        directory (Path): Directory being processed.
        exclude_file (Optional[Path]): Path to exclusion rules file.
        streaming_complete (bool): Whether all streaming operations have finished.

    Example:
        >>> # Initialize analyzer (with skip to avoid filesystem dependency)
        >>> analyzer = StreamingDir2Text("src")  # doctest: +SKIP
        >>> # Stream tree first - partial metrics available
        >>> for line in analyzer.stream_tree():  # doctest: +SKIP
        ...     print(line, end='')  # Each line includes newline
        src/
        ├── file1.txt
        └── subdir/
            └── file2.txt
        >>> print(f"Tree metrics: {analyzer.line_count}")  # doctest: +SKIP
        Tree metrics: 4
    """

    def __init__(
        self,
        directory: Union[str, Path],
        *,
        exclude_file: Optional[Union[str, Path]] = None,
        output_format: str = "xml",
        tokenizer_model: Optional[str] = None,
    ):
        """Initialize streaming directory analysis.

        Args:
            directory: Directory to process
            exclude_file: Optional path to exclusion rules file (e.g., .gitignore)
            output_format: Format for output ('xml' or 'json')
            tokenizer_model: Model to use for token counting. If None, token counting is disabled.

        Raises:
            ValueError: If directory is invalid or output format is unsupported
            FileNotFoundError: If directory or exclude_file doesn't exist
        """
        # Validate inputs
        self.directory = Path(directory)
        if not self.directory.is_dir():
            raise ValueError(f"'{directory}' is not a valid directory")

        self.exclude_file = Path(exclude_file) if exclude_file else None
        if self.exclude_file and not self.exclude_file.is_file():
            raise FileNotFoundError(f"Exclusion file not found: {self.exclude_file}")

        if output_format not in ("xml", "json"):
            raise ValueError(f"Unsupported output format: {output_format}")

        # Initialize components
        self._exclusion_rules = GitIgnoreExclusionRules(str(self.exclude_file)) if self.exclude_file else None
        self._fs_tree = FileSystemTree(str(self.directory), self._exclusion_rules)

        # Only create token counter if model is specified
        self._token_counter = TokenCounter(model=tokenizer_model) if tokenizer_model is not None else None

        # Setup output strategy
        self._strategy: OutputStrategy
        if output_format == "xml":
            self._strategy = XMLOutputStrategy()
        else:
            self._strategy = JSONOutputStrategy()

        self._content_printer = FileContentPrinter(self._fs_tree, self._strategy, tokenizer=self._token_counter)

        # Initialize metrics - these are immediately available
        self._directory_count = self._fs_tree.get_directory_count()
        self._file_count = self._fs_tree.get_file_count()

        # These accumulate during streaming
        self._line_count = 0
        self._character_count = 0
        self._token_count = 0

        # Track streaming state
        self._tree_complete = False
        self._contents_complete = False

    def _update_metrics(self, text: str, token_count: Optional[int] = None) -> None:
        """Update metrics with new content.

        Args:
            text: The text content to update metrics for.
            token_count: Optional token count if already calculated.
        """
        self._line_count += text.count("\n")
        self._character_count += len(text)
        if token_count is not None:
            self._token_count += token_count

    @property
    def directory_count(self) -> int:
        """Number of directories (excluding root).

        This count is final and available immediately after construction.

        Returns:
            int: Number of directories in the tree, excluding the root directory.
        """
        return self._directory_count

    @property
    def file_count(self) -> int:
        """Number of files.

        This count is final and available immediately after construction.

        Returns:
            int: Number of files in the tree.
        """
        return self._file_count

    @property
    def streaming_complete(self) -> bool:
        """Whether all streaming operations have completed.

        When True, all metrics represent final values. When False, metrics
        represent only the content processed so far.

        Returns:
            bool: True if all streaming operations are complete.
        """
        return self._tree_complete and self._contents_complete

    @property
    def line_count(self) -> int:
        """Number of lines processed in the current streaming operation.

        This count accumulates during streaming. The value is partial until
        streaming_complete is True.

        Returns:
            int: Current count of lines processed.
        """
        return self._line_count

    @property
    def character_count(self) -> int:
        """Number of characters processed in the current streaming operation.

        This count accumulates during streaming. The value is partial until
        streaming_complete is True.

        Returns:
            int: Current count of characters processed.
        """
        return self._character_count

    @property
    def token_count(self) -> int:
        """Number of tokens processed in the current streaming operation.

        This count accumulates during streaming. The value is partial until
        streaming_complete is True.

        Returns:
            int: Current count of tokens processed.
        """
        return self._token_count

    def stream_tree(self) -> Iterator[str]:
        """Stream the directory tree representation line by line.

        Returns:
            Iterator yielding lines of the tree representation.

        Raises:
            RuntimeError: If tree has already been streamed.

        Note:
            - Can only be called once
            - Updates metrics incrementally as content is streamed
            - Each yielded line includes a trailing newline

        Example:
            >>> tree = StreamingDir2Text(".")  # doctest: +SKIP
            >>> for line in tree.stream_tree():  # doctest: +SKIP
            ...     print(line, end='')  # line already includes newline
            ./
            ├── file1.txt
            └── file2.txt
        """
        if self._tree_complete:
            raise RuntimeError("Tree has already been streamed")

        for line in self._fs_tree.stream_tree_representation():
            line_with_newline = line + "\n"
            token_count = self._token_counter.count_tokens(line_with_newline) if self._token_counter else None
            self._update_metrics(line_with_newline, token_count)
            yield line_with_newline

        final_newline = "\n"
        token_count = self._token_counter.count_tokens(final_newline) if self._token_counter else None
        self._update_metrics(final_newline, token_count)
        yield final_newline
        self._tree_complete = True

    def stream_contents(self) -> Iterator[str]:
        """Stream file contents chunk by chunk.

        Returns:
            Iterator yielding chunks of file contents in the specified format.

        Raises:
            RuntimeError: If contents have already been streamed.

        Note:
            - Can only be called once
            - Updates metrics incrementally as content is streamed

        Example:
            >>> analyzer = StreamingDir2Text(".")  # doctest: +SKIP
            >>> for chunk in analyzer.stream_contents():  # doctest: +SKIP
            ...     print(chunk, end='')  # Process content chunks
        """
        if self._contents_complete:
            raise RuntimeError("Contents have already been streamed")

        for _, _, content_iter in self._content_printer.yield_file_contents():
            for chunk in content_iter:
                self._update_metrics(chunk)
                yield chunk
            yield "\n"
        self._contents_complete = True


class Dir2Text(StreamingDir2Text):
    """Complete directory analyzer that processes everything immediately.

    This class extends StreamingDir2Text but processes all content during initialization,
    storing the results for immediate access. This approach provides simpler access to
    directory content but requires enough memory to hold the complete output.

    Memory Usage Note:
        This class loads and stores complete file contents in memory during initialization.
        For large directories or files, this can require significant memory. If memory
        usage is a concern, use the StreamingDir2Text parent class instead.

    Example:
        >>> # Everything is processed during initialization (doctest skipped for filesystem)
        >>> analyzer = Dir2Text("src")  # doctest: +SKIP
        >>> print(analyzer.tree_string)  # doctest: +SKIP
        src/
        ├── file1.txt
        └── file2.txt
    """

    def __init__(
        self,
        directory: Union[str, Path],
        *,
        exclude_file: Optional[Union[str, Path]] = None,
        output_format: str = "xml",
        tokenizer_model: str = "gpt-4",
    ):
        """Initialize and immediately process the entire directory.

        Args:
            directory: Directory to process
            exclude_file: Optional path to exclusion rules file (e.g., .gitignore)
            output_format: Format for output ('xml' or 'json')
            tokenizer_model: Model to use for token counting

        Raises:
            ValueError: If directory is invalid or output format is unsupported
            FileNotFoundError: If directory or exclude_file doesn't exist
        """
        super().__init__(
            directory, exclude_file=exclude_file, output_format=output_format, tokenizer_model=tokenizer_model
        )

        # Process everything immediately
        self._tree_string = "".join(self.stream_tree())
        self._content_string = "".join(self.stream_contents())
        # Now streaming_complete is True and all metrics are final

    @property
    def tree_string(self) -> str:
        """Complete tree representation as a string.

        Returns:
            str: The complete tree representation.
        """
        return self._tree_string

    @property
    def content_string(self) -> str:
        """Complete file contents as a string.

        Returns:
            str: The complete file contents.
        """
        return self._content_string
