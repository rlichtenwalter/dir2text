"""Tools for chunk-based file reading operations."""

from typing import Iterator, TextIO


class ChunkedFileReader:
    """Iterator-based chunked file reader that breaks on whitespace boundaries.

    This class provides a memory-efficient way to read files in chunks while ensuring
    chunks end at whitespace boundaries when possible. This is particularly useful for
    text processing tasks like token counting where word boundaries matter.

    The reader maintains a small buffer of content that didn't fit in the previous chunk
    due to whitespace boundary requirements. This content is prepended to the next chunk.

    Args:
        file_obj: An opened text file object to read from. The file should already be
            configured with appropriate encoding and error handling settings.
        chunk_size: Size of chunks to read in bytes. Must be at least 4096 bytes.
            Defaults to 65536 (64 KB).

    Raises:
        ValueError: If chunk_size is less than 4096 bytes.
        TypeError: If file_obj is not a text file object.

    Example:
        >>> with open('myfile.txt', 'r', encoding='utf-8') as f:  # doctest: +SKIP
        ...     reader = ChunkedFileReader(f)
        ...     for chunk in reader:
        ...         process_chunk(chunk)
    """

    MINIMUM_CHUNK_SIZE = 4096  # 4 KB

    def __init__(self, file_obj: TextIO, chunk_size: int = 65536) -> None:
        """Initialize the chunked reader with a file object and chunk size."""

        if chunk_size < self.MINIMUM_CHUNK_SIZE:
            raise ValueError(f"chunk_size must be at least {self.MINIMUM_CHUNK_SIZE} bytes, " f"got {chunk_size}")

        self._file: TextIO = file_obj
        self._chunk_size: int = chunk_size
        self._buffer: str = ""

    def __iter__(self) -> Iterator[str]:
        """Return self as iterator."""
        return self

    def __next__(self) -> str:
        """Get the next chunk of content, breaking at whitespace when possible.

        Returns:
            A string containing the next chunk of file content. The chunk will end
            at a whitespace boundary unless no whitespace is found in the chunk.

        Raises:
            StopIteration: When the end of the file is reached.
            UnicodeError: If there are encoding issues when reading the file.
        """
        # First, check if we have content in the buffer
        content: str = self._buffer

        # Read the next chunk
        chunk: str = self._file.read(self._chunk_size)
        if not chunk:
            if content:
                self._buffer = ""
                return content
            raise StopIteration

        content += chunk

        # If we have content, try to find the last whitespace
        if content:
            # Find last whitespace character
            for i in range(len(content) - 1, -1, -1):
                if content[i].isspace():
                    # Split at this whitespace character
                    self._buffer = content[i + 1 :]  # noqa: E203
                    return content[: i + 1]

        # If no whitespace found or content is empty, return everything
        self._buffer = ""
        return content
