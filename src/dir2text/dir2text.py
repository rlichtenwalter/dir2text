"""Directory to text conversion with streaming support.

This module provides classes for converting directory structures to text format,
with support for streaming output and token counting. It includes both streaming
and complete processing implementations.
"""

from pathlib import Path
from typing import Iterator, Optional, Union

from dir2text.exceptions import TokenizationError
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.file_content_printer import FileContentPrinter
from dir2text.file_system_tree import FileSystemTree, PermissionAction
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

    Note:
        The doctest examples are marked with SKIP because they require a specific
        filesystem structure that can't be guaranteed in the test environment. The
        examples are still valid and demonstrate proper usage.

    Attributes:
        directory (Path): Directory being processed.
        exclude_file (Optional[Path]): Path to exclusion rules file.
        streaming_complete (bool): Whether all streaming operations have finished.

    Example:
        >>> # Initialize analyzer (requires actual filesystem structure)
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

    Raises:
        ValueError: If directory is invalid or output format is unsupported.
        FileNotFoundError: If directory or exclude_file doesn't exist.
        PermissionError: If access is denied and permission_action is "raise".
        TokenizationError: If token counting is enabled but tokenizer initialization fails.
    """

    def __init__(
        self,
        directory: Union[str, Path],
        *,
        exclude_file: Optional[Union[str, Path]] = None,
        output_format: str = "xml",
        tokenizer_model: Optional[str] = None,
        permission_action: Union[str, PermissionAction] = PermissionAction.IGNORE,
    ):
        """Initialize streaming directory analysis.

        Args:
            directory: Directory to process
            exclude_file: Optional path to exclusion rules file (e.g., .gitignore)
            output_format: Format for output ('xml' or 'json')
            tokenizer_model: Model to use for counting. If None, token counting is disabled.
            permission_action: How to handle permission errors during traversal.
                Can be either "ignore" or "raise", or a PermissionAction enum value.
                Defaults to "ignore".

        Raises:
            ValueError: If directory is invalid or output format is unsupported
            FileNotFoundError: If directory or exclude_file doesn't exist
            PermissionError: If access is denied and permission_action is "raise"
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

        # Handle permission_action input
        if isinstance(permission_action, str):
            try:
                permission_action = PermissionAction(permission_action.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid permission_action: {permission_action}. " "Must be one of: 'ignore', 'raise'"
                )

        # Initialize components
        self._exclusion_rules = GitIgnoreExclusionRules(str(self.exclude_file)) if self.exclude_file else None
        self._fs_tree = FileSystemTree(str(self.directory), self._exclusion_rules, permission_action=permission_action)

        # Create counter if counting is enabled
        self._counter = TokenCounter(model=tokenizer_model) if tokenizer_model is not None else None

        # Setup output strategy
        self._strategy: OutputStrategy
        if output_format == "xml":
            self._strategy = XMLOutputStrategy()
        else:
            self._strategy = JSONOutputStrategy()

        self._content_printer = FileContentPrinter(self._fs_tree, self._strategy, tokenizer=self._counter)

        # Initialize metrics that are immediately available
        self._directory_count = self._fs_tree.get_directory_count()
        self._file_count = self._fs_tree.get_file_count()

        # Track streaming state
        self._tree_complete = False
        self._contents_complete = False

    @property
    def directory_count(self) -> int:
        """Number of directories (excluding root).

        This count is final and available immediately after construction.

        Returns:
            int: Number of directories in the tree, excluding the root directory.

        Example:
            >>> tree = StreamingDir2Text("src")  # doctest: +SKIP
            >>> tree.directory_count  # doctest: +SKIP
            5
        """
        return self._directory_count

    @property
    def file_count(self) -> int:
        """Number of files.

        This count is final and available immediately after construction.

        Returns:
            int: Number of files in the tree.

        Example:
            >>> tree = StreamingDir2Text("src")  # doctest: +SKIP
            >>> tree.file_count  # doctest: +SKIP
            42
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
    def token_count(self) -> int:
        """Number of tokens processed across all operations.

        Returns:
            int: Total count of tokens processed. Returns 0 if token counting is disabled
                (i.e., if tokenizer_model was None during initialization).

        Example:
            >>> tree = StreamingDir2Text("src")  # doctest: +SKIP
            >>> tree.token_count  # doctest: +SKIP
            1500
        """
        return self._counter.get_total_tokens() if self._counter is not None else 0

    @property
    def line_count(self) -> int:
        """Number of lines processed across all operations.

        This count accumulates during streaming. The value is partial until
        streaming_complete is True. Returns 0 if token counting is disabled.

        Returns:
            int: Total count of lines processed. Returns 0 if token counting is disabled
                (i.e., if tokenizer_model was None during initialization).

        Example:
            >>> tree = StreamingDir2Text("src")  # doctest: +SKIP
            >>> tree.line_count  # doctest: +SKIP
            250
        """
        return self._counter.get_total_lines() if self._counter is not None else 0

    @property
    def character_count(self) -> int:
        """Number of characters processed across all operations.

        This count accumulates during streaming. The value is partial until
        streaming_complete is True. Returns 0 if token counting is disabled.

        Returns:
            int: Total count of characters processed. Returns 0 if token counting is disabled
                (i.e., if tokenizer_model was None during initialization).

        Example:
            >>> tree = StreamingDir2Text("src")  # doctest: +SKIP
            >>> tree.character_count  # doctest: +SKIP
            15000
        """
        return self._counter.get_total_characters() if self._counter is not None else 0

    def _yield(self, text: str) -> str:
        """Return text for yielding.

        Helper method to provide a means of outputting text.

        Args:
            text: Text to count and yield.

        Returns:
            The input text, unchanged.
        """
        return text

    def _count_and_yield(self, text: str) -> str:
        """Count text and return it for yielding.

        Helper method to ensure consistent counting of output text.

        Args:
            text: Text to count and yield.

        Returns:
            The input text, unchanged.
        """
        if self._counter is not None:
            try:
                self._counter.count(text)
            except TokenizationError:
                # Continue even if token counting fails
                pass
        return self._yield(text)

    def stream_tree(self) -> Iterator[str]:
        """Stream the directory tree representation line by line.

        Returns:
            Iterator yielding lines of the tree representation.

        Raises:
            RuntimeError: If tree has already been streamed.
            PermissionError: If access is denied and permission_action is "raise".

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
            yield self._count_and_yield(line_with_newline)

        final_newline = "\n"
        yield self._count_and_yield(final_newline)
        self._tree_complete = True

    def stream_contents(self) -> Iterator[str]:
        """Stream file contents chunk by chunk.

        Returns:
            Iterator yielding chunks of file contents in the specified format.

        Raises:
            RuntimeError: If contents have already been streamed.
            PermissionError: If access is denied and permission_action is "raise".

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

        for file_path, relative_path, content_iter in self._content_printer.yield_file_contents():
            # Output file content
            for chunk in content_iter:
                yield self._yield(chunk)

            # Add separator newline
            yield self._count_and_yield("\n")

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
        >>> # Everything is processed during initialization (requires filesystem)
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
        permission_action: Union[str, PermissionAction] = PermissionAction.IGNORE,
    ):
        """Initialize and immediately process the entire directory.

        Args:
            directory: Directory to process
            exclude_file: Optional path to exclusion rules file (e.g., .gitignore)
            output_format: Format for output ('xml' or 'json')
            tokenizer_model: Model to use for token counting
            permission_action: How to handle permission errors during traversal.
                Can be either "ignore" or "raise", or a PermissionAction enum value.
                Defaults to "ignore".

        Raises:
            ValueError: If directory is invalid or output format is unsupported
            FileNotFoundError: If directory or exclude_file doesn't exist
            PermissionError: If access is denied and permission_action is "raise"
        """
        super().__init__(
            directory,
            exclude_file=exclude_file,
            output_format=output_format,
            tokenizer_model=tokenizer_model,
            permission_action=permission_action,
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
