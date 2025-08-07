"""Unit tests for the FileContentPrinter class.

Tests both normal operation and error handling scenarios.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dir2text.exceptions import BinaryFileError
from dir2text.file_content_printer import FileContentPrinter
from dir2text.file_system_tree.binary_action import BinaryAction
from dir2text.file_system_tree.file_system_tree import FileSystemTree
from dir2text.output_strategies.json_strategy import JSONOutputStrategy
from dir2text.output_strategies.xml_strategy import XMLOutputStrategy
from dir2text.token_counter import CountResult


@pytest.fixture
def temp_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple file structure
        base_dir = Path(tmpdir)

        # ASCII text file
        ascii_file = base_dir / "ascii.txt"
        ascii_file.write_text("Hello, world!")

        # UTF-8 text file
        utf8_file = base_dir / "utf8.txt"
        utf8_file.write_text("Hello, 世界!")

        # Latin-1 text file
        latin1_file = base_dir / "latin1.txt"
        latin1_file.write_bytes("Hello, é!".encode("latin-1"))

        # Binary-like file
        binary_file = base_dir / "binary.dat"
        binary_file.write_bytes(bytes(range(256)))

        yield base_dir


@pytest.fixture
def temp_directory_with_symlinks():
    """Create a temporary directory with symlinks for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create a file
        file1 = base_dir / "file1.txt"
        file1.write_text("Test file content")

        # Try to create a symlink
        try:
            symlink1 = base_dir / "link1.txt"
            os.symlink(file1, symlink1)
            has_symlinks = True
        except (OSError, NotImplementedError, NameError):
            # If symlink creation fails, we'll mark the test to be skipped
            has_symlinks = False

        yield base_dir, has_symlinks


@pytest.fixture
def mock_tree():
    """Create a mock FileSystemTree."""
    return MagicMock(spec=FileSystemTree)


@pytest.fixture
def mock_tree_with_symlinks():
    """Create a mock FileSystemTree with simulated symlinks."""
    mock = MagicMock(spec=FileSystemTree)

    # Set up follow_symlinks property
    mock.follow_symlinks = False

    # Set up iterate_files to return a single file
    mock.iterate_files.return_value = [("/abs/path/file.txt", "file.txt")]

    # Set up iterate_symlinks to return a symlink
    mock.iterate_symlinks.return_value = [("/abs/path/link.txt", "link.txt", "./file.txt")]

    return mock


@pytest.fixture
def mock_token_counter():
    """Create a mock token counter with token counting capability."""
    counter = MagicMock()
    counter.count.return_value = CountResult(lines=1, tokens=10, characters=20)
    counter.get_total_tokens.return_value = 10
    return counter


@pytest.fixture
def mock_token_counter_no_tokens():
    """Create a mock token counter without token counting capability."""
    counter = MagicMock()
    counter.count.return_value = CountResult(lines=1, tokens=None, characters=20)
    counter.get_total_tokens.return_value = None
    return counter


def test_init_default_parameters(mock_tree):
    """Test initialization with default parameters."""
    printer = FileContentPrinter(mock_tree)
    assert printer.encoding == "utf-8"
    assert printer.errors == "strict"
    assert isinstance(printer.output_strategy, XMLOutputStrategy)


def test_init_custom_parameters(mock_tree):
    """Test initialization with custom parameters."""
    printer = FileContentPrinter(mock_tree, output_format="json", encoding="latin-1", errors="replace")
    assert printer.encoding == "latin-1"
    assert printer.errors == "replace"
    assert isinstance(printer.output_strategy, JSONOutputStrategy)


def test_init_with_strategy_instance(mock_tree):
    """Test initialization with a strategy instance."""
    strategy = JSONOutputStrategy()
    printer = FileContentPrinter(mock_tree, output_format=strategy)
    assert printer.output_strategy is strategy


def test_init_invalid_output_format(mock_tree):
    """Test initialization with invalid output format."""
    with pytest.raises(ValueError) as exc_info:
        FileContentPrinter(mock_tree, output_format="yaml")
    assert "Unsupported output format" in str(exc_info.value)


def test_init_invalid_output_format_type(mock_tree):
    """Test initialization with invalid output format type."""
    with pytest.raises(TypeError) as exc_info:
        FileContentPrinter(mock_tree, output_format=123)
    assert "must be either a string" in str(exc_info.value)


def test_init_invalid_errors_parameter(mock_tree):
    """Test initialization with invalid errors parameter."""
    with pytest.raises(ValueError) as exc_info:
        FileContentPrinter(mock_tree, errors="invalid")
    assert "Invalid error handler" in str(exc_info.value)


def test_init_invalid_encoding(mock_tree):
    """Test initialization with invalid encoding."""
    with pytest.raises(LookupError) as exc_info:
        FileContentPrinter(mock_tree, encoding="invalid-encoding")
    assert "not available" in str(exc_info.value)


def test_process_ascii_file(temp_directory):
    """Test processing a simple ASCII file."""
    tree = FileSystemTree(str(temp_directory))
    printer = FileContentPrinter(tree)

    # Process files
    processed = list(printer.yield_file_contents())

    # Find ascii.txt in processed files
    ascii_file = next((item for item in processed if item[1].endswith("ascii.txt")), None)
    assert ascii_file is not None

    # Check content
    content = "".join(list(ascii_file[2]))
    assert "Hello, world!" in content


def test_process_utf8_file(temp_directory):
    """Test processing a UTF-8 file."""
    tree = FileSystemTree(str(temp_directory))
    printer = FileContentPrinter(tree)

    processed = list(printer.yield_file_contents())
    utf8_file = next((item for item in processed if item[1].endswith("utf8.txt")), None)
    assert utf8_file is not None

    content = "".join(list(utf8_file[2]))
    assert "Hello, 世界!" in content


def test_process_latin1_file_with_correct_encoding(temp_directory):
    """Test processing a Latin-1 file with correct encoding."""
    tree = FileSystemTree(str(temp_directory))
    printer = FileContentPrinter(tree, encoding="latin-1")

    processed = list(printer.yield_file_contents())
    latin1_file = next((item for item in processed if item[1].endswith("latin1.txt")), None)
    assert latin1_file is not None

    content = "".join(list(latin1_file[2]))
    assert "Hello, é!" in content


def test_process_latin1_file_with_wrong_encoding(temp_directory):
    """Test processing a Latin-1 file with wrong encoding."""
    tree = FileSystemTree(str(temp_directory))
    printer = FileContentPrinter(tree)

    with pytest.raises(ValueError):
        # Consume all content to trigger the read
        for _, _, content_iter in printer.yield_file_contents():
            list(content_iter)


def test_process_with_ignore_errors(temp_directory):
    """Test processing with errors='ignore'."""
    tree = FileSystemTree(str(temp_directory))
    printer = FileContentPrinter(tree, errors="ignore")

    # Should not raise any exceptions
    processed = list(printer.yield_file_contents())
    assert len(processed) > 0


def test_process_with_replace_errors(temp_directory):
    """Test processing with errors='replace'."""
    tree = FileSystemTree(str(temp_directory))
    printer = FileContentPrinter(tree, errors="replace")

    # Should not raise any exceptions
    processed = list(printer.yield_file_contents())
    assert len(processed) > 0


def test_file_not_found_error(mock_tree):
    """Test handling of missing files."""
    mock_tree.iterate_files.return_value = [("/nonexistent", "nonexistent")]

    with patch("builtins.open", side_effect=FileNotFoundError("No such file")):
        printer = FileContentPrinter(mock_tree)
        with pytest.raises(OSError):
            for _, _, content_iter in printer.yield_file_contents():
                list(content_iter)


def test_permission_error(temp_directory):
    """Test handling of permission errors."""
    # Create a file with no read permissions
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        tree = FileSystemTree(str(temp_directory))
        printer = FileContentPrinter(tree)

        with pytest.raises(OSError):
            for _, _, content_iter in printer.yield_file_contents():
                list(content_iter)


def test_get_output_file_extension():
    """Test getting the output file extension."""
    tree = MagicMock(spec=FileSystemTree)

    # Test XML strategy
    printer = FileContentPrinter(tree, output_format="xml")
    assert printer.get_output_file_extension() == ".xml"

    # Test JSON strategy
    printer = FileContentPrinter(tree, output_format="json")
    assert printer.get_output_file_extension() == ".json"


def test_yield_file_contents_with_symlinks(mock_tree_with_symlinks):
    """Test processing files and symlinks."""
    # Create a printer with the mock tree that has both files and symlinks
    printer = FileContentPrinter(mock_tree_with_symlinks, output_format="xml")

    # Get all content (files and symlinks)
    content_items = list(printer.yield_file_contents())

    # Should have both a file and a symlink
    assert len(content_items) == 2

    # The first item should be a file
    file_item = content_items[0]
    assert file_item[1] == "file.txt"

    # The second item should be a symlink
    symlink_item = content_items[1]
    assert symlink_item[1] == "link.txt"

    # Check that the symlink content is a single item
    symlink_content = list(symlink_item[2])
    assert len(symlink_content) == 1
    assert "<symlink" in symlink_content[0]
    assert 'path="link.txt"' in symlink_content[0]
    assert 'target="./file.txt"' in symlink_content[0]


def test_symlink_output_format(mock_tree_with_symlinks):
    """Test symlink output in different formats."""
    # Test XML format
    xml_printer = FileContentPrinter(mock_tree_with_symlinks, output_format="xml")
    xml_items = list(xml_printer.yield_file_contents())
    xml_symlink = xml_items[1]
    xml_content = list(xml_symlink[2])

    assert "<symlink" in xml_content[0]
    assert "/>" in xml_content[0]

    # Test JSON format
    json_printer = FileContentPrinter(mock_tree_with_symlinks, output_format="json")
    json_items = list(json_printer.yield_file_contents())
    json_symlink = json_items[1]
    json_content = list(json_symlink[2])

    assert '"type": "symlink"' in json_content[0]
    assert '"path": "link.txt"' in json_content[0]
    assert '"target": "./file.txt"' in json_content[0]


def test_follow_symlinks_behavior(mock_tree):
    """Test that when follow_symlinks=True, no symlinks are processed."""
    # Configure mock to follow symlinks
    mock_tree.follow_symlinks = True
    mock_tree.iterate_files.return_value = [("/abs/path/file.txt", "file.txt")]
    mock_tree.iterate_symlinks.return_value = []  # Empty when following symlinks

    printer = FileContentPrinter(mock_tree)
    content_items = list(printer.yield_file_contents())

    # Should only have files, no symlinks
    assert len(content_items) == 1
    assert content_items[0][1] == "file.txt"


def test_real_symlinks_in_output(temp_directory_with_symlinks):
    """Test processing real symlinks on the filesystem."""
    base_dir, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Create a tree with the real directory structure
    tree = FileSystemTree(str(base_dir))
    printer = FileContentPrinter(tree)

    # Get all content
    content_items = list(printer.yield_file_contents())

    # Should have both a file and a symlink
    assert len(content_items) == 2

    # Find the file and symlink entries
    file_item = next((item for item in content_items if item[1] == "file1.txt"), None)
    symlink_item = next((item for item in content_items if item[1] == "link1.txt"), None)

    assert file_item is not None
    assert symlink_item is not None

    # Check file content
    file_content = "".join(list(file_item[2]))
    assert "Test file content" in file_content

    # Check symlink content
    symlink_content = "".join(list(symlink_item[2]))
    assert "<symlink" in symlink_content
    assert "link1.txt" in symlink_content


def test_count_file_tokens_with_tokenizer(mock_tree, mock_token_counter):
    """Test _count_file_tokens method with tokenizer available."""
    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch("dir2text.file_content_printer.ChunkedFileReader") as mock_reader,
    ):
        # Set up mocks
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_reader.return_value = ["chunk1", "chunk2"]

        printer = FileContentPrinter(mock_tree, tokenizer=mock_token_counter)
        tokens = printer._count_file_tokens("/test/file.py", "file.py")

        # Verify tokens were counted
        assert tokens == 20  # 10 tokens per chunk, 2 chunks


def test_count_file_tokens_without_tokenizer(mock_tree, mock_token_counter_no_tokens):
    """Test _count_file_tokens method without tokenizer."""
    printer = FileContentPrinter(mock_tree, tokenizer=mock_token_counter_no_tokens)
    tokens = printer._count_file_tokens("/test/file.py", "file.py")

    # Verify no tokens were counted
    assert tokens is None


def test_yield_wrapped_content_with_tokens(mock_tree, mock_token_counter):
    """Test _yield_wrapped_content method with token counting."""
    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch("dir2text.file_content_printer.ChunkedFileReader") as mock_reader,
        patch.object(FileContentPrinter, "_count_file_tokens", return_value=10),
    ):
        # Set up mocks
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_reader.return_value = ["chunk1", "chunk2"]

        printer = FileContentPrinter(mock_tree, output_format="xml", tokenizer=mock_token_counter)
        content = list(printer._yield_wrapped_content("/test/file.py", "file.py"))

        # Verify tokens were included
        assert 'tokens="10"' in content[0]


def test_yield_wrapped_content_without_tokens(mock_tree, mock_token_counter_no_tokens):
    """Test _yield_wrapped_content method without token counting."""
    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch("dir2text.file_content_printer.ChunkedFileReader") as mock_reader,
    ):
        # Set up mocks
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_reader.return_value = ["chunk1", "chunk2"]

        printer = FileContentPrinter(mock_tree, output_format="xml", tokenizer=mock_token_counter_no_tokens)
        content = list(printer._yield_wrapped_content("/test/file.py", "file.py"))

        # Verify tokens were not included
        assert "tokens=" not in content[0]


def test_always_counts_lines_and_characters(mock_tree, mock_token_counter_no_tokens):
    """Test that lines and characters are always counted, even without token counting."""
    with (
        patch("builtins.open", MagicMock()) as mock_open,
        patch("dir2text.file_content_printer.ChunkedFileReader") as mock_reader,
    ):
        # Set up mocks
        mock_open.return_value.__enter__.return_value = MagicMock()
        mock_reader.return_value = ["chunk1", "chunk2"]

        printer = FileContentPrinter(mock_tree, tokenizer=mock_token_counter_no_tokens)
        list(printer._yield_wrapped_content("/test/file.py", "file.py"))

        # Verify lines and characters were counted
        assert mock_token_counter_no_tokens.count.call_count == 2  # Called for each chunk


class TestBinaryFileHandling:
    """Test binary file handling with different binary actions."""

    def test_binary_action_ignore(self, temp_directory):
        """Test that binary files are ignored when binary_action is IGNORE."""
        tree = FileSystemTree(temp_directory)
        printer = FileContentPrinter(tree, binary_action=BinaryAction.IGNORE)

        # Collect all file contents
        contents = list(printer.yield_file_contents())

        # Binary file should be skipped, so it won't appear in the results
        file_paths = [rel_path for _, rel_path, _ in contents]
        assert "binary.dat" not in file_paths
        assert "ascii.txt" in file_paths  # Text files should still be included

    def test_binary_action_raise(self, temp_directory):
        """Test that binary files raise BinaryFileError when binary_action is RAISE."""
        tree = FileSystemTree(temp_directory)
        printer = FileContentPrinter(tree, binary_action=BinaryAction.RAISE)

        with pytest.raises(BinaryFileError) as exc_info:
            # Try to process all files - should fail on binary file when content is consumed
            for file_path, rel_path, content_iter in printer.yield_file_contents():
                # Actually consume the content iterator - this will trigger the exception
                list(content_iter)

        # Check that the error contains the binary file path
        assert "binary.dat" in str(exc_info.value)

    def test_binary_action_encode(self, temp_directory):
        """Test that binary files are base64 encoded when binary_action is ENCODE."""
        tree = FileSystemTree(temp_directory)
        printer = FileContentPrinter(tree, binary_action=BinaryAction.ENCODE)

        # Find the binary file content
        binary_content = None
        for file_path, rel_path, content_iter in printer.yield_file_contents():
            if rel_path == "binary.dat":
                # Collect all content chunks
                content_chunks = list(content_iter)
                binary_content = "".join(content_chunks)
                break

        assert binary_content is not None, "Binary file content should be found"

        # Check that it contains base64-encoded content
        # The content should start with XML/JSON wrapper and contain base64 data
        assert "binary.dat [binary]" in binary_content
        # Base64 content should be present (base64 uses A-Z, a-z, 0-9, +, /)
        import re

        base64_pattern = re.compile(r"[A-Za-z0-9+/]")
        assert base64_pattern.search(binary_content), "Should contain base64 encoded data"

    def test_binary_action_encode_xml_format(self, temp_directory):
        """Test binary encoding with XML output format."""
        tree = FileSystemTree(temp_directory)
        printer = FileContentPrinter(tree, output_format="xml", binary_action=BinaryAction.ENCODE)

        # Find binary file content
        binary_content = None
        for file_path, rel_path, content_iter in printer.yield_file_contents():
            if rel_path == "binary.dat":
                binary_content = "".join(content_iter)
                break

        assert binary_content is not None
        # Should have XML-style formatting
        assert "<file" in binary_content
        assert "</file>" in binary_content
        assert "[binary]" in binary_content

    def test_binary_action_encode_json_format(self, temp_directory):
        """Test binary encoding with JSON output format."""
        tree = FileSystemTree(temp_directory)
        printer = FileContentPrinter(tree, output_format="json", binary_action=BinaryAction.ENCODE)

        # Find binary file content
        binary_content = None
        for file_path, rel_path, content_iter in printer.yield_file_contents():
            if rel_path == "binary.dat":
                binary_content = "".join(content_iter)
                break

        assert binary_content is not None
        # Should have JSON-style formatting
        assert '"path"' in binary_content
        assert '"content"' in binary_content
        assert "[binary]" in binary_content

    def test_text_files_unaffected_by_binary_action(self, temp_directory):
        """Test that text files are processed normally regardless of binary_action."""
        tree = FileSystemTree(temp_directory)

        for action in [BinaryAction.IGNORE, BinaryAction.ENCODE]:
            printer = FileContentPrinter(tree, binary_action=action)

            # Find text file content
            text_content = None
            for file_path, rel_path, content_iter in printer.yield_file_contents():
                if rel_path == "ascii.txt":
                    text_content = "".join(content_iter)
                    break

            assert text_content is not None
            assert "Hello, world!" in text_content

    def test_binary_detection_accuracy(self, temp_directory):
        """Test that binary detection correctly identifies binary vs text files."""
        from dir2text.file_system_tree.binary_detector import is_binary_file

        # Test our fixture files
        assert not is_binary_file(temp_directory / "ascii.txt")
        assert not is_binary_file(temp_directory / "utf8.txt")
        assert is_binary_file(temp_directory / "binary.dat")

    @patch("dir2text.file_system_tree.binary_detector.is_binary_file")
    def test_binary_detection_error_handling(self, mock_is_binary, temp_directory):
        """Test behavior when binary detection fails."""
        # Make binary detection raise an OSError
        mock_is_binary.side_effect = OSError("Permission denied")

        tree = FileSystemTree(temp_directory)
        printer = FileContentPrinter(tree, binary_action=BinaryAction.IGNORE)

        # Should fall back to treating as text file
        contents = list(printer.yield_file_contents())

        # All files should be processed (binary detection failure doesn't stop processing)
        file_paths = [rel_path for _, rel_path, _ in contents]
        assert len(file_paths) > 0

    def test_empty_binary_file(self, temp_directory):
        """Test handling of empty files (which should be treated as text)."""
        # Create an empty file
        empty_file = temp_directory / "empty.bin"
        empty_file.touch()

        tree = FileSystemTree(temp_directory)
        printer = FileContentPrinter(tree, binary_action=BinaryAction.RAISE)

        # Empty file should not raise BinaryFileError
        contents = list(printer.yield_file_contents())
        file_paths = [rel_path for _, rel_path, _ in contents]
        assert "empty.bin" in file_paths

    def test_binary_action_with_custom_output_strategy(self, temp_directory):
        """Test binary action with custom output strategy."""
        from dir2text.output_strategies.json_strategy import JSONOutputStrategy

        tree = FileSystemTree(temp_directory)
        custom_strategy = JSONOutputStrategy()
        printer = FileContentPrinter(tree, output_format=custom_strategy, binary_action=BinaryAction.ENCODE)

        # Should work with custom strategy
        contents = list(printer.yield_file_contents())
        file_paths = [rel_path for _, rel_path, _ in contents]

        # Text files should be included
        assert "ascii.txt" in file_paths

        # Binary file should be included and base64 encoded
        binary_content = None
        for file_path, rel_path, content_iter in contents:
            if rel_path == "binary.dat":
                binary_content = "".join(content_iter)
                break

        assert binary_content is not None
        assert '"content"' in binary_content  # JSON format

    def test_binary_token_counting_comprehensive(self, temp_directory):
        """Test that token counting works correctly for base64-encoded binary files."""
        from unittest.mock import MagicMock

        # Create a binary file with known content
        binary_file = temp_directory / "test.bin"
        binary_content = bytes(range(64))  # 64 bytes of data
        binary_file.write_bytes(binary_content)

        tree = FileSystemTree(temp_directory)

        # Test with mock tokenizer that requires tokens in start tag
        mock_tokenizer_start = MagicMock()
        mock_tokenizer_start.get_total_tokens.return_value = 100  # Indicates token counting is enabled
        mock_tokenizer_start.count.return_value = MagicMock()
        mock_tokenizer_start.count.return_value.tokens = 10  # Mock: each base64 chunk = 10 tokens

        printer_start = FileContentPrinter(tree, binary_action=BinaryAction.ENCODE, tokenizer=mock_tokenizer_start)

        # Mock output strategy that requires tokens in start tag
        printer_start.output_strategy = MagicMock()
        printer_start.output_strategy.requires_tokens_in_start = True
        printer_start.output_strategy.format_start.return_value = "<start tokens=10>"
        printer_start.output_strategy.format_content.return_value = "base64_content"
        printer_start.output_strategy.format_end.return_value = "</end>"

        # Process file - should pre-count tokens for start tag
        contents = list(printer_start.yield_file_contents())

        # Find our binary file among the processed files
        binary_content = None
        for file_path, rel_path, content_iter in contents:
            if rel_path == "test.bin":
                content_chunks = list(content_iter)
                binary_content = (file_path, rel_path, content_chunks)
                break

        assert binary_content is not None, "Binary file should be processed"
        file_path, rel_path, content_chunks = binary_content

        # Verify start tag received token count (pre-counted)
        printer_start.output_strategy.format_start.assert_called_with("test.bin [binary]", "binary", 10)

        # Verify _count_binary_file_tokens was called for pre-counting
        assert mock_tokenizer_start.count.called

        # Test with tokenizer that doesn't require tokens in start tag (streaming mode)
        mock_tokenizer_stream = MagicMock()
        mock_tokenizer_stream.get_total_tokens.return_value = 100
        mock_tokenizer_stream.count.return_value = MagicMock()
        mock_tokenizer_stream.count.return_value.tokens = 5  # Mock: each formatted chunk = 5 tokens

        printer_stream = FileContentPrinter(tree, binary_action=BinaryAction.ENCODE, tokenizer=mock_tokenizer_stream)

        # Mock output strategy that doesn't require tokens in start tag
        printer_stream.output_strategy = MagicMock()
        printer_stream.output_strategy.requires_tokens_in_start = False
        printer_stream.output_strategy.format_start.return_value = "<start>"
        printer_stream.output_strategy.format_content.return_value = "base64_content"
        printer_stream.output_strategy.format_end.return_value = "</end>"

        # Process file - should stream and accumulate tokens
        contents = list(printer_stream.yield_file_contents())

        # Find our binary file among the processed files
        binary_content = None
        for file_path, rel_path, content_iter in contents:
            if rel_path == "test.bin":
                content_chunks = list(content_iter)
                binary_content = (file_path, rel_path, content_chunks)
                break

        assert binary_content is not None, "Binary file should be processed"
        file_path, rel_path, content_chunks = binary_content

        # Verify start tag received None (no pre-counting)
        printer_stream.output_strategy.format_start.assert_called_with("test.bin [binary]", "binary", None)

        # Verify end tag received accumulated token count
        # Note: exact count depends on base64 encoding, but should be > 0
        end_call_args = printer_stream.output_strategy.format_end.call_args
        if end_call_args and end_call_args[0]:  # If called with arguments
            token_count = end_call_args[0][0]
            assert token_count > 0, "Streaming token count should be accumulated"

        # Verify streaming token counting was called
        assert mock_tokenizer_stream.count.called

    def test_binary_token_counting_integration(self, temp_directory):
        """Integration test for binary token counting with real tokenizer."""
        from unittest.mock import MagicMock

        # Create a small binary file with actual binary data
        binary_file = temp_directory / "small.bin"
        binary_file.write_bytes(bytes(range(256))[:50])  # 50 bytes of binary data

        tree = FileSystemTree(temp_directory)

        # Use real tokenizer interface but mock the counting
        mock_tokenizer = MagicMock()
        mock_tokenizer.get_total_tokens.return_value = None  # Indicates no total tracking

        # Mock count method to return realistic token counts for base64 content
        def mock_count(text):
            result = MagicMock()
            result.tokens = len(text) // 4  # Simple mock: ~1 token per 4 chars
            return result

        mock_tokenizer.count.side_effect = mock_count

        printer = FileContentPrinter(tree, binary_action=BinaryAction.ENCODE, tokenizer=mock_tokenizer)

        # Process and verify token counting works end-to-end
        total_content = ""
        for file_path, rel_path, content_iter in printer.yield_file_contents():
            if rel_path == "small.bin":
                total_content = "".join(content_iter)
                break

        assert total_content != ""
        assert "small.bin [binary]" in total_content
        # Verify tokenizer was called (tokens were counted for base64 content)
        assert mock_tokenizer.count.called
