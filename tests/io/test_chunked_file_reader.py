"""Unit tests for the ChunkedFileReader class."""

import io

import pytest

from dir2text.io.chunked_file_reader import ChunkedFileReader


def test_basic_chunked_reading() -> None:
    """Test basic functionality with simple text."""
    # Create text larger than minimum chunk size
    base_text = "Hello world! This is a test. " * 200  # ~5000 chars
    text = base_text * 3  # ~15000 chars
    file_obj = io.StringIO(text)
    reader = ChunkedFileReader(file_obj, chunk_size=4096)

    chunks = list(reader)
    assert "".join(chunks) == text
    assert len(chunks) > 1  # Should have multiple chunks


def test_whitespace_boundary() -> None:
    """Test that chunks break at whitespace boundaries when possible."""
    # Create patterned text with predictable whitespace
    pattern = "abcdef ghijkl mnopqr stuvwx yz1234 "  # 30 chars with spaces
    text = pattern * 200  # 6000 chars
    file_obj = io.StringIO(text)
    reader = ChunkedFileReader(file_obj, chunk_size=4096)

    chunks = list(reader)
    # Each chunk should end with a space
    assert all(chunk.endswith(" ") for chunk in chunks[:-1])
    # When joined, should reconstruct original text
    assert "".join(chunks) == text


def test_no_whitespace() -> None:
    """Test handling of text with no whitespace."""
    # Create long string with no whitespace
    text = "x" * 10000
    file_obj = io.StringIO(text)
    reader = ChunkedFileReader(file_obj, chunk_size=4096)

    chunks = list(reader)
    assert "".join(chunks) == text


def test_empty_file() -> None:
    """Test handling of empty file."""
    file_obj = io.StringIO("")
    reader = ChunkedFileReader(file_obj)

    chunks = list(reader)
    assert len(chunks) == 0


def test_only_whitespace() -> None:
    """Test handling of file with only whitespace."""
    # Create large whitespace file
    text = " \n\t " * 2000  # 8000 whitespace chars
    file_obj = io.StringIO(text)
    reader = ChunkedFileReader(file_obj, chunk_size=4096)

    chunks = list(reader)
    assert "".join(chunks) == text


def test_chunk_size_validation() -> None:
    """Test that invalid chunk sizes are rejected."""
    file_obj = io.StringIO("test")

    with pytest.raises(ValueError) as exc_info:
        ChunkedFileReader(file_obj, chunk_size=2048)  # Less than minimum
    assert "chunk_size must be at least" in str(exc_info.value)


def test_iterator_protocol() -> None:
    """Test that the class properly implements iterator protocol."""
    text = "test text " * 1000  # 10000 chars
    file_obj = io.StringIO(text)
    reader = ChunkedFileReader(file_obj, chunk_size=4096)

    # Should be able to use in for loop
    result = ""
    for chunk in reader:
        result += chunk
    assert result == text

    # Second iteration should produce no content
    assert list(reader) == []


def test_large_chunks() -> None:
    """Test handling of chunk size larger than content."""
    text = "small text " * 500  # 5000 chars
    file_obj = io.StringIO(text)
    reader = ChunkedFileReader(file_obj, chunk_size=10000)

    chunks = list(reader)
    assert chunks[0] == text  # Should be returned in a single chunk


def test_exact_chunk_size() -> None:
    """Test handling of text exactly matching chunk size."""
    text = "x" * 4096
    file_obj = io.StringIO(text)
    reader = ChunkedFileReader(file_obj, chunk_size=4096)

    chunks = list(reader)
    assert len(chunks) == 1
    assert len(chunks[0]) == 4096
