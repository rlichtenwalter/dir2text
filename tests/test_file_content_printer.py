"""Unit tests for the FileContentPrinter class.

Tests both normal operation and error handling scenarios.
"""

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
def mock_tree():
    """Create a mock FileSystemTree."""
    return MagicMock(spec=FileSystemTree)


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
