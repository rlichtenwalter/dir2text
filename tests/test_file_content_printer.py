"""Unit tests for the FileContentPrinter class.

Tests both normal operation and error handling scenarios.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dir2text.file_content_printer import FileContentPrinter
from dir2text.file_system_tree import FileSystemTree
from dir2text.output_strategies.json_strategy import JSONOutputStrategy
from dir2text.output_strategies.xml_strategy import XMLOutputStrategy


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
