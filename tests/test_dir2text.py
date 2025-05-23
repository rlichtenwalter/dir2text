"""Unit tests for the dir2text.py module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dir2text.dir2text import Dir2Text, StreamingDir2Text
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.token_counter import CountResult


@pytest.fixture
def mock_token_counter():
    """Create a mock token counter for testing that simulates accumulation."""
    counter = MagicMock()
    # Track running totals
    counter._token_total = 0
    counter._line_total = 0
    counter._char_total = 0

    # Make count method increment the totals
    def count_side_effect(text):
        tokens_per_call = 10
        lines_per_call = 1
        chars_per_call = 20

        counter._token_total += tokens_per_call
        counter._line_total += lines_per_call
        counter._char_total += chars_per_call

        return CountResult(tokens=tokens_per_call, lines=lines_per_call, characters=chars_per_call)

    counter.count.side_effect = count_side_effect

    # Make getter methods return the current totals
    counter.get_total_tokens.side_effect = lambda: counter._token_total
    counter.get_total_lines.side_effect = lambda: counter._line_total
    counter.get_total_characters.side_effect = lambda: counter._char_total

    return counter


@pytest.fixture
def mock_token_counter_no_tokens():
    """Create a mock token counter with no token counting capability."""
    counter = MagicMock()
    # Track running totals (no tokens)
    counter._line_total = 0
    counter._char_total = 0

    # Make count method increment the totals but return None for tokens
    def count_side_effect(text):
        lines_per_call = 1
        chars_per_call = 20

        counter._line_total += lines_per_call
        counter._char_total += chars_per_call

        return CountResult(tokens=None, lines=lines_per_call, characters=chars_per_call)

    counter.count.side_effect = count_side_effect

    # Make getter methods return the current totals
    counter.get_total_tokens.return_value = None
    counter.get_total_lines.side_effect = lambda: counter._line_total
    counter.get_total_characters.side_effect = lambda: counter._char_total

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

    # Test with exclusion rules
    rules = GitIgnoreExclusionRules()
    rules.add_rule("*.pyc")
    analyzer = StreamingDir2Text(temp_directory, exclusion_rules=rules)
    assert analyzer._exclusion_rules is rules


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


def test_streaming_dir2text_with_exclusion_rules(temp_directory):
    """Test with exclusion rules to filter files."""
    # Create rules from .gitignore content
    rules = GitIgnoreExclusionRules()
    rules.add_rule("*.pyc")

    analyzer = StreamingDir2Text(temp_directory, exclusion_rules=rules)
    content_output = "".join(analyzer.stream_contents())

    # Verify .pyc file is excluded
    assert "compiled python" not in content_output

    # Verify other files are included
    assert "def main():" in content_output
    assert "# Test Project" in content_output


def test_streaming_dir2text_with_multiple_exclusion_rules(temp_directory):
    """Test with multiple exclusion patterns."""
    # Create rules with multiple patterns
    rules = GitIgnoreExclusionRules()
    rules.add_rule("*.pyc")  # Exclude .pyc files
    rules.add_rule("*.md")  # Exclude markdown files

    analyzer = StreamingDir2Text(temp_directory, exclusion_rules=rules)
    content_output = "".join(analyzer.stream_contents())

    # Verify .pyc file is excluded
    assert "compiled python" not in content_output

    # Verify .md file is excluded
    assert "# Test Project" not in content_output

    # Verify other files are included
    assert "def main():" in content_output


def test_streaming_dir2text_exclusion_order(temp_directory):
    """Test that exclusion order matters for overriding patterns."""
    # Create rules for testing negation patterns - Order 1
    rules1 = GitIgnoreExclusionRules()
    rules1.add_rule("src/*.py")  # Exclude all Python files in src
    rules1.add_rule("!src/main.py")  # But allow main.py

    # Order 1: exclude all .py, then allow main.py
    analyzer1 = StreamingDir2Text(temp_directory, exclusion_rules=rules1)
    content_output1 = "".join(analyzer1.stream_contents())

    # Create rules for testing negation patterns - Order 2
    rules2 = GitIgnoreExclusionRules()
    rules2.add_rule("!src/main.py")  # Try to allow main.py
    rules2.add_rule("src/*.py")  # Then exclude all .py

    # Order 2: allow main.py, then exclude all .py (this won't work as expected)
    analyzer2 = StreamingDir2Text(temp_directory, exclusion_rules=rules2)
    content_output2 = "".join(analyzer2.stream_contents())

    # With order 1, main.py should be included
    assert "def main():" in content_output1

    # With order 2, main.py will be excluded (negation first doesn't work)
    assert "def main():" not in content_output2


def test_streaming_dir2text_with_complex_exclusions(temp_directory):
    """Test with more complex exclusion patterns including negations."""
    rules = GitIgnoreExclusionRules()
    rules.add_rule("*.pyc")  # Exclude .pyc files
    rules.add_rule("src/utils/")  # Exclude utils directory
    rules.add_rule("!src/utils/helpers.py")  # But include helpers.py

    analyzer = StreamingDir2Text(temp_directory, exclusion_rules=rules)
    content_output = "".join(analyzer.stream_contents())

    # Verify .pyc file is excluded
    assert "compiled python" not in content_output

    # Verify utils/ is excluded but helpers.py is included (with negation)
    assert "def helper():" in content_output


def test_streaming_dir2text_with_token_counting(temp_directory, mock_token_counter):
    """Test integration with token counter."""
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter):
        analyzer = StreamingDir2Text(temp_directory, tokenizer_model="gpt-4")
        list(analyzer.stream_tree())
        list(analyzer.stream_contents())

        # We should have multiple chunks of content counted, each adding tokens
        # The exact number doesn't matter as long as it's consistent with the mock
        assert analyzer.token_count > 0
        assert analyzer.line_count > 0
        assert analyzer.character_count > 0


def test_streaming_dir2text_no_token_counting(temp_directory, mock_token_counter_no_tokens):
    """Test behavior when token counting is disabled."""
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter_no_tokens):
        analyzer = StreamingDir2Text(temp_directory)
        list(analyzer.stream_tree())
        list(analyzer.stream_contents())
        assert analyzer.token_count is None
        assert analyzer.line_count > 0
        assert analyzer.character_count > 0


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


def test_dir2text_with_exclusion_rules(temp_directory):
    """Test Dir2Text with exclusion rules."""
    # Create rules with multiple patterns
    rules = GitIgnoreExclusionRules()
    rules.add_rule("*.pyc")  # Exclude .pyc files
    rules.add_rule("*.md")  # Exclude markdown files

    analyzer = Dir2Text(temp_directory, exclusion_rules=rules)

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


def test_streaming_dir2text_exclusion_rules_with_patterns(temp_directory):
    """Test exclusion rules with direct patterns."""
    # Create a rules object with multiple patterns
    rules = GitIgnoreExclusionRules()
    rules.add_rule("*.pyc")  # Exclude .pyc files
    rules.add_rule("*.md")  # Exclude markdown files
    rules.add_rule("!README.md")  # But include README.md

    analyzer = StreamingDir2Text(temp_directory, exclusion_rules=rules)
    content_output = "".join(analyzer.stream_contents())

    # Verify .pyc file is excluded
    assert "compiled python" not in content_output

    # Verify README.md is included (negation pattern works)
    assert "# Test Project" in content_output


def test_streaming_dir2text_exclusion_rules_ordering(temp_directory):
    """Test that pattern ordering is preserved with exclusion rules object."""
    # Order 1: Exclude Python files, then allow main.py
    rules1 = GitIgnoreExclusionRules()
    rules1.add_rule("src/*.py")  # Exclude all Python files in src
    rules1.add_rule("!src/main.py")  # But allow main.py

    # Order 2: Allow main.py, then exclude all Python files
    rules2 = GitIgnoreExclusionRules()
    rules2.add_rule("!src/main.py")  # Try to allow main.py
    rules2.add_rule("src/*.py")  # Then exclude all Python files in src

    # Check with order 1
    analyzer1 = StreamingDir2Text(temp_directory, exclusion_rules=rules1)
    content_output1 = "".join(analyzer1.stream_contents())

    # Check with order 2
    analyzer2 = StreamingDir2Text(temp_directory, exclusion_rules=rules2)
    content_output2 = "".join(analyzer2.stream_contents())

    # With order 1, main.py should be included (negation works)
    assert "def main():" in content_output1

    # With order 2, main.py will be excluded (later rule wins)
    assert "def main():" not in content_output2


def test_tokenizer_model_none(temp_directory, mock_token_counter_no_tokens):
    """Test that token_count is None when tokenizer_model is None."""
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter_no_tokens):
        analyzer = StreamingDir2Text(temp_directory, tokenizer_model=None)
        list(analyzer.stream_tree())
        list(analyzer.stream_contents())
        assert analyzer.token_count is None
        assert analyzer.line_count > 0
        assert analyzer.character_count > 0


def test_line_character_count_without_tokenizing(temp_directory, mock_token_counter_no_tokens):
    """Test that line and character counts still work when tokenizer_model is None."""
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter_no_tokens):
        analyzer = StreamingDir2Text(temp_directory)
        list(analyzer.stream_tree())
        list(analyzer.stream_contents())
        assert analyzer.token_count is None
        assert analyzer.line_count > 0
        assert analyzer.character_count > 0


def test_dir2text_with_token_counting(temp_directory, mock_token_counter):
    """Test Dir2Text with token counting enabled."""
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter):
        analyzer = Dir2Text(temp_directory, tokenizer_model="gpt-4")
        assert analyzer.token_count > 0
        assert analyzer.line_count > 0
        assert analyzer.character_count > 0


def test_dir2text_without_token_counting(temp_directory, mock_token_counter_no_tokens):
    """Test Dir2Text without token counting."""
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter_no_tokens):
        analyzer = Dir2Text(temp_directory)
        assert analyzer.token_count is None
        assert analyzer.line_count > 0
        assert analyzer.character_count > 0


def test_counting_in_all_modes(temp_directory, mock_token_counter):
    """Test that counting happens in both streaming and complete modes."""
    with patch("dir2text.dir2text.TokenCounter", return_value=mock_token_counter):
        # Test streaming mode
        analyzer1 = StreamingDir2Text(temp_directory, tokenizer_model="gpt-4")
        list(analyzer1.stream_tree())
        list(analyzer1.stream_contents())
        assert analyzer1.line_count > 0
        assert analyzer1.character_count > 0
        assert analyzer1.token_count > 0

        # Test complete mode
        analyzer2 = Dir2Text(temp_directory, tokenizer_model="gpt-4")
        assert analyzer2.line_count > 0
        assert analyzer2.character_count > 0
        assert analyzer2.token_count > 0
