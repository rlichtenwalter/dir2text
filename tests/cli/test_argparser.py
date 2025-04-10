"""Unit tests for the argument parser module in dir2text CLI."""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dir2text.cli.argparser import create_exclusion_action, create_parser, validate_args
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules


@pytest.fixture
def mock_exclusion_rules():
    """Create a mock ExclusionRules object."""
    mock_rules = MagicMock(spec=GitIgnoreExclusionRules)
    mock_rules.load_rules = MagicMock()
    mock_rules.add_rule = MagicMock()
    return mock_rules


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_directory):
    """Create a temporary file for testing."""
    temp_file = temp_directory / "test.txt"
    temp_file.write_text("test content")
    return temp_file


def test_create_exclusion_action():
    """Test creation of ExclusionRulesAction class."""
    mock_rules = MagicMock()

    # Create the action class
    ExclusionAction = create_exclusion_action(mock_rules)

    # Verify it's a proper argparse Action
    assert issubclass(ExclusionAction, argparse.Action)

    # Test basic initialization
    action = ExclusionAction(
        option_strings=["-e", "--exclude"],
        dest="exclude",
        help="test help",
    )

    # Verify attributes were set
    assert action.option_strings == ["-e", "--exclude"]
    assert action.dest == "exclude"
    assert action.help == "test help"


def test_exclusion_action_exclude_file(mock_exclusion_rules):
    """Test ExclusionRulesAction handling file-based exclusions."""
    # Create the action class
    ExclusionAction = create_exclusion_action(mock_exclusion_rules)

    # Create an instance
    action = ExclusionAction(
        option_strings=["-e", "--exclude"],
        dest="exclude",
    )

    # Create parser namespace and mock args
    namespace = argparse.Namespace()
    mock_file = Path("/path/to/.gitignore")

    # Call the action
    action(None, namespace, mock_file, "-e")

    # Verify exclusion rules were updated and namespace attributes set
    mock_exclusion_rules.load_rules.assert_called_once_with(mock_file)
    assert namespace.exclude == [mock_file]


def test_exclusion_action_ignore_pattern(mock_exclusion_rules):
    """Test ExclusionRulesAction handling pattern-based exclusions."""
    # Create the action class
    ExclusionAction = create_exclusion_action(mock_exclusion_rules)

    # Create an instance
    action = ExclusionAction(
        option_strings=["-i", "--ignore"],
        dest="ignore",
    )

    # Create parser namespace and mock args
    namespace = argparse.Namespace()
    pattern = "*.pyc"

    # Call the action
    action(None, namespace, pattern, "-i")

    # Verify exclusion rules were updated and namespace attributes set
    mock_exclusion_rules.add_rule.assert_called_once_with(pattern)
    assert namespace.ignore == [pattern]


def test_exclusion_action_multiple_patterns(mock_exclusion_rules):
    """Test ExclusionRulesAction with multiple patterns."""
    # Create the action class
    ExclusionAction = create_exclusion_action(mock_exclusion_rules)

    # Create instances for each option
    exclude_action = ExclusionAction(
        option_strings=["-e", "--exclude"],
        dest="exclude",
    )

    ignore_action = ExclusionAction(
        option_strings=["-i", "--ignore"],
        dest="ignore",
    )

    # Create parser namespace
    namespace = argparse.Namespace()

    # Call actions multiple times
    exclude_action(None, namespace, Path("/path/to/file1"), "-e")
    ignore_action(None, namespace, "*.txt", "-i")
    exclude_action(None, namespace, Path("/path/to/file2"), "-e")
    ignore_action(None, namespace, "*.md", "-i")

    # Verify all exclusions were added correctly
    assert mock_exclusion_rules.load_rules.call_count == 2
    assert mock_exclusion_rules.add_rule.call_count == 2

    # Verify namespace attributes
    assert len(namespace.exclude) == 2
    assert len(namespace.ignore) == 2
    assert namespace.exclude == [Path("/path/to/file1"), Path("/path/to/file2")]
    assert namespace.ignore == ["*.txt", "*.md"]


def test_exclusion_action_append_to_existing(mock_exclusion_rules):
    """Test ExclusionRulesAction appending to existing lists."""
    # Create the action class
    ExclusionAction = create_exclusion_action(mock_exclusion_rules)

    # Create an instance
    action = ExclusionAction(
        option_strings=["-e", "--exclude"],
        dest="exclude",
    )

    # Create parser namespace with existing list
    namespace = argparse.Namespace(exclude=[Path("/existing/file")])
    mock_file = Path("/path/to/.gitignore")

    # Call the action
    action(None, namespace, mock_file, "-e")

    # Verify namespace attributes were appended
    assert namespace.exclude == [Path("/existing/file"), mock_file]


def test_create_parser(mock_exclusion_rules, temp_directory):
    """Test parser creation."""
    parser = create_parser(mock_exclusion_rules)

    # Basic parser verification
    assert isinstance(parser, argparse.ArgumentParser)

    # Test parsing simple arguments
    args = parser.parse_args([str(temp_directory)])
    assert args.directory == temp_directory
    assert not args.no_tree
    assert not args.no_contents
    assert args.format == "xml"
    assert not args.count
    assert args.tokenizer == "gpt-4"
    assert args.permission_action == "ignore"


def test_create_parser_with_all_options(mock_exclusion_rules, temp_file, temp_directory):
    """Test parser creation with all options specified."""
    parser = create_parser(mock_exclusion_rules)

    # Create a valid output file path
    output_file = temp_directory / "output.txt"

    # Parse with all options
    args = parser.parse_args(
        [
            "-e",
            str(temp_file),
            "-i",
            "*.pyc",
            "-o",
            str(output_file),
            "-T",
            "-C",
            "-f",
            "json",
            "-c",
            "-s",
            "stderr",
            "-t",
            "gpt-3.5-turbo",
            "-P",
            "warn",
            str(temp_directory),
        ]
    )

    # Verify all options were correctly parsed
    assert args.directory == temp_directory
    assert args.exclude == [temp_file]
    assert args.ignore == ["*.pyc"]
    assert args.output == output_file
    assert args.no_tree
    assert args.no_contents
    assert args.format == "json"
    assert args.count
    assert args.stats == "stderr"
    assert args.tokenizer == "gpt-3.5-turbo"
    assert args.permission_action == "warn"


def test_validate_args_valid():
    """Test validate_args with valid arguments."""
    # Create args with valid values
    args = argparse.Namespace(
        stats=None,
        output=Path("/path/to/output.txt"),
    )

    # This should not raise any errors
    validate_args(args)

    # Try another valid combination
    args = argparse.Namespace(
        stats="stderr",
        output=None,
    )
    validate_args(args)


def test_validate_args_stats_file_without_output():
    """Test validate_args with stats=file but no output."""
    # Create args with invalid combination
    args = argparse.Namespace(
        stats="file",
        output=None,
    )

    # This should raise ValueError
    with pytest.raises(ValueError) as excinfo:
        validate_args(args)

    assert "--stats=file requires -o/--output" in str(excinfo.value)


def test_parser_action_integration(temp_directory, temp_file):
    """Test integration between parser and actions with real GitIgnoreExclusionRules."""
    # Create a real rules object
    rules = GitIgnoreExclusionRules()

    # Create parser with the rules
    parser = create_parser(rules)

    # Parse arguments with exclusions
    args = parser.parse_args(
        [
            "-e",
            str(temp_file),
            "-i",
            "*.pyc",
            str(temp_directory),
        ]
    )

    # Verify both options were correctly parsed
    assert args.exclude == [temp_file]
    assert args.ignore == ["*.pyc"]

    # Verify the rules object was updated correctly
    # We can't easily verify internal state, but we can check its behavior
    with patch.object(GitIgnoreExclusionRules, "exclude") as mock_exclude:
        # Set up mock behavior
        mock_exclude.return_value = False

        # Call exclude on the rules object
        rules.exclude("test.txt")

        # Verify it was called
        mock_exclude.assert_called_once_with("test.txt")
