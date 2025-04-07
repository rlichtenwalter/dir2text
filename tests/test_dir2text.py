"""Unit tests for the dir2text.py module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dir2text.dir2text import Dir2Text, StreamingDir2Text


@pytest.fixture
def mock_token_counter():
    """Create a mock token counter for testing."""
    counter = MagicMock()
    counter.count.return_value = MagicMock(tokens=10, lines=1, characters=20)
    return counter


@pytest.fixture
def temp_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create directories
        (base_dir / "src").mkdir()
        (base_dir / "src/utils").mkdir()
        (base_dir / "docs").mkdir()

        # Create test files
        (base_dir / "src/main.py").write_text("def main():\n    print('Hello')\n")
        (base_dir / "src/utils/helpers.py").write_text("def helper():\n    pass\n")
        (base_dir / "docs/README.md").write_text("# Test Project\nDescription.\n")
        (base_dir / "src/main.pyc").write_bytes(b"compiled python")

        # Create .gitignore
        (base_dir / ".gitignore").write_text("*.pyc\n")

        # Create .npmignore
        (base_dir / ".npmignore").write_text("*.md\n")

        # Create custom ignore file
        (base_dir / "custom.ignore").write_text("src/utils/\n!src/utils/helpers.py\n")

        yield base_dir


def test_streaming_dir2text_initialization(temp_directory):
    """Test basic initialization of StreamingDir2Text."""
    # Test default initialization
    analyzer = StreamingDir2Text(temp_directory)
    assert analyzer.directory == temp_directory
    assert analyzer.exclude_files is None

    # Test with one exclusion file
    gitignore = temp_directory / ".gitignore"
    analyzer = StreamingDir2Text(temp_directory, exclude_files=gitignore)
    assert analyzer.exclude_files == [gitignore]

    # Test with a list of exclusion files
    gitignore = temp_directory / ".gitignore"
    npmignore = temp_directory / ".npmignore"
    analyzer = StreamingDir2Text(temp_directory, exclude_files=[gitignore, npmignore])
    assert analyzer.exclude_files == [gitignore, npmignore]


def test_streaming_dir2text_invalid_directory():
    """Test initialization with invalid directory."""
    with pytest.raises(ValueError):
        StreamingDir2Text("/nonexistent/directory")


def test_streaming_dir2text_invalid_format():
    """Test initialization with invalid output format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            StreamingDir2Text(tmpdir, output_format="invalid")


def test_streaming_dir2text_metrics(temp_directory):
    """Test metrics tracking in StreamingDir2Text."""
    analyzer = StreamingDir2Text(temp_directory)

    # Initial metrics
    assert analyzer.directory_count > 0
    assert analyzer.file_count > 0
    assert not analyzer.streaming_complete

    # After streaming tree
    list(analyzer.stream_tree())
    assert not analyzer.streaming_complete

    # After streaming contents
    list(analyzer.stream_contents())
    assert analyzer.streaming_complete


def test_streaming_dir2text_tree_output(temp_directory):
    """Test tree visualization output."""
    analyzer = StreamingDir2Text(temp_directory)
    tree_output = "".join(analyzer.stream_tree())

    # Verify structure
    assert str(temp_directory.name) in tree_output
    assert "src/" in tree_output
    assert "docs/" in tree_output
    assert "main.py" in tree_output
    assert "README.md" in tree_output


def test_streaming_dir2text_content_output(temp_directory):
    """Test file content streaming."""
    analyzer = StreamingDir2Text(temp_directory)
    content_output = "".join(analyzer.stream_contents())

    # Verify content
    assert "def main():" in content_output
    assert "# Test Project" in content_output


def test_streaming_dir2text_with_single_exclusion(temp_directory):
    """Test with a single exclusion file."""
    gitignore = temp_directory / ".gitignore"
    analyzer = StreamingDir2Text(temp_directory, exclude_files=gitignore)
    content_output = "".join(analyzer.stream_contents())

    # Verify .pyc file is excluded
    assert "compiled python" not in content_output

    # Verify other files are included
    assert "def main():" in content_output
    assert "# Test Project" in content_output


def test_streaming_dir2text_with_multiple_exclusions(temp_directory):
    """Test with multiple exclusion files working together."""
    gitignore = temp_directory / ".gitignore"
    npmignore = temp_directory / ".npmignore"
    analyzer = StreamingDir2Text(temp_directory, exclude_files=[gitignore, npmignore])
    content_output = "".join(analyzer.stream_contents())

    # Verify .pyc file is excluded (from gitignore)
    assert "compiled python" not in content_output

    # Verify .md file is excluded (from npmignore)
    assert "# Test Project" not in content_output

    # Verify other files are included
    assert "def main():" in content_output


def test_streaming_dir2text_exclusion_order(temp_directory):
    """Test that exclusion order matters for overriding patterns."""
    # Create files for testing negation patterns
    custom_ignore_a = temp_directory / "custom_a.ignore"
    custom_ignore_a.write_text("src/*.py\n")  # Exclude all Python files in src

    custom_ignore_b = temp_directory / "custom_b.ignore"
    custom_ignore_b.write_text("!src/main.py\n")  # But allow main.py

    # Order 1: exclude all .py, then allow main.py
    analyzer1 = StreamingDir2Text(temp_directory, exclude_files=[custom_ignore_a, custom_ignore_b])
    content_output1 = "".join(analyzer1.stream_contents())

    # Order 2: allow main.py, then exclude all .py (this won't work as expected)
    analyzer2 = StreamingDir2Text(temp_directory, exclude_files=[custom_ignore_b, custom_ignore_a])
    content_output2 = "".join(analyzer2.stream_contents())

    # With order 1, main.py should be included
    assert "def main():" in content_output1

    # With order 2, main.py will be excluded (negation first doesn't work)
    assert "def main():" not in content_output2


def test_streaming_dir2text_with_complex_exclusions(temp_directory):
    """Test with more complex exclusion patterns including negations."""
    gitignore = temp_directory / ".gitignore"
    custom_ignore = temp_directory / "custom.ignore"

    analyzer = StreamingDir2Text(temp_directory, exclude_files=[gitignore, custom_ignore])
    content_output = "".join(analyzer.stream_contents())

    # Verify .pyc file is excluded (from gitignore)
    assert "compiled python" not in content_output

    # Verify utils/ is excluded but helpers.py is included (custom.ignore with negation)
    assert "def helper():" in content_output


def test_streaming_dir2text_with_token_counting(temp_directory, mock_token_counter):
    """Test integration with token counter."""
    mock_token_counter.get_total_tokens.return_value = 42  # Set return value
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter):
        analyzer = StreamingDir2Text(temp_directory, tokenizer_model="gpt-4")
        list(analyzer.stream_tree())
        list(analyzer.stream_contents())
        assert analyzer.token_count > 0


def test_streaming_dir2text_output_formats(temp_directory):
    """Test different output formats."""
    # Test XML format
    analyzer = StreamingDir2Text(temp_directory, output_format="xml")
    content = "".join(analyzer.stream_contents())
    assert content.startswith("<file")
    assert "</file>" in content

    # Test JSON format
    analyzer = StreamingDir2Text(temp_directory, output_format="json")
    content = "".join(analyzer.stream_contents())
    assert '"path":' in content
    assert '"content":' in content


def test_dir2text_complete_processing(temp_directory):
    """Test Dir2Text complete processing."""
    analyzer = Dir2Text(temp_directory)

    assert analyzer.tree_string
    assert analyzer.content_string
    assert analyzer.streaming_complete


def test_dir2text_with_multiple_exclusions(temp_directory):
    """Test Dir2Text with multiple exclusion files."""
    gitignore = temp_directory / ".gitignore"
    npmignore = temp_directory / ".npmignore"

    analyzer = Dir2Text(temp_directory, exclude_files=[gitignore, npmignore])

    # Verify .pyc file and .md file are excluded
    assert "compiled python" not in analyzer.content_string
    assert "# Test Project" not in analyzer.content_string

    # Verify Python files are included
    assert "def main():" in analyzer.content_string


def test_streaming_reuse_prevention(temp_directory):
    """Test prevention of reusing streams."""
    analyzer = StreamingDir2Text(temp_directory)

    # First usage should work
    list(analyzer.stream_tree())
    list(analyzer.stream_contents())

    # Second usage should fail
    with pytest.raises(RuntimeError):
        list(analyzer.stream_tree())
    with pytest.raises(RuntimeError):
        list(analyzer.stream_contents())


def test_empty_directory():
    """Test handling of empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analyzer = StreamingDir2Text(tmpdir)
        tree_output = "".join(analyzer.stream_tree())
        content_output = "".join(analyzer.stream_contents())

        assert os.path.basename(tmpdir) in tree_output  # Check basename instead
        assert not content_output  # Empty directory has no content
        assert analyzer.file_count == 0
        assert analyzer.directory_count == 0


def test_unicode_handling(temp_directory):
    """Test handling of Unicode filenames and content."""
    # Create file with Unicode name and content
    unicode_file = temp_directory / "测试.txt"
    unicode_file.write_text("Hello 世界!")

    analyzer = StreamingDir2Text(temp_directory)
    tree_output = "".join(analyzer.stream_tree())
    content_output = "".join(analyzer.stream_contents())

    assert "测试.txt" in tree_output
    assert "Hello 世界!" in content_output


def test_nonexistent_exclusion_files(temp_directory):
    """Test that nonexistent exclusion files raise errors."""
    with pytest.raises(FileNotFoundError):
        StreamingDir2Text(temp_directory, exclude_files=["nonexistent.ignore"])

    # Test with mix of valid and invalid files
    with pytest.raises(FileNotFoundError):
        gitignore = temp_directory / ".gitignore"
        StreamingDir2Text(temp_directory, exclude_files=[gitignore, "nonexistent.ignore"])
