import os
import tempfile
from pathlib import Path

import pytest

from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules


@pytest.fixture
def temp_gitignore():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("*.txt\n")
        f.write("!important.txt\n")
        f.write("subdir/\n")
        f.write("*.py[cod]\n")
        f.write("**/__pycache__/\n")
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_npmignore():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("*.log\n")
        f.write("node_modules/\n")
        f.write("!important.log\n")
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_customignore():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("*.json\n")
        f.write("!important.json\n")
        f.write("dist/\n")
    yield f.name
    os.unlink(f.name)


def create_absolute_path(path):
    return str(Path("/absolute/path").joinpath(path))


@pytest.mark.parametrize(
    "path,expected",
    [
        # Test relative paths
        ("file.txt", True),
        ("important.txt", False),
        ("file.py", False),
        ("subdir/file.py", True),
        # Test absolute paths
        (create_absolute_path("file.txt"), True),
        (create_absolute_path("important.txt"), False),
        (create_absolute_path("file.py"), False),
        (create_absolute_path("subdir/file.py"), True),
        # Additional tests
        ("subdir/important.txt", True),
        ("another_dir/file.txt", True),
        ("another_dir/file.py", False),
        # Edge cases
        ("nested/subdir/file.txt", True),
        ("file.pyc", True),
        ("__pycache__/cache_file.py", True),
        ("lib/__pycache__/cache_file.py", True),
    ],
)
def test_gitignore_exclusion_rules(temp_gitignore, path, expected):
    rules = GitIgnoreExclusionRules(temp_gitignore)
    assert rules.exclude(path) == expected, f"Failed for path: {path}"


def test_gitignore_exclusion_rules_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        pass
    try:
        rules = GitIgnoreExclusionRules(f.name)
        assert not rules.exclude("any_file.txt"), "Empty .gitignore should not exclude any files"
    finally:
        os.unlink(f.name)


def test_gitignore_exclusion_rules_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        GitIgnoreExclusionRules("nonexistent_file")


def test_multiple_exclusion_files(temp_gitignore, temp_npmignore):
    """Test combining patterns from multiple exclusion files."""
    rules = GitIgnoreExclusionRules([temp_gitignore, temp_npmignore])

    # Test patterns from first file
    assert rules.exclude("file.txt")
    assert not rules.exclude("important.txt")
    assert rules.exclude("file.pyc")

    # Test patterns from second file
    assert rules.exclude("debug.log")
    assert not rules.exclude("important.log")
    assert rules.exclude("node_modules/package.json")


def test_multiple_exclusion_files_order(temp_gitignore, temp_npmignore, temp_customignore):
    """Test that the order of exclusion files matters for negated patterns."""
    # Order 1: gitignore then customignore
    rules1 = GitIgnoreExclusionRules([temp_gitignore, temp_customignore])
    # Order 2: customignore then gitignore
    rules2 = GitIgnoreExclusionRules([temp_customignore, temp_gitignore])

    # Test case: important.txt
    # In gitignore: *.txt then !important.txt
    # In customignore: no mention of *.txt
    # Expected: not excluded regardless of order
    assert not rules1.exclude("important.txt")
    assert not rules2.exclude("important.txt")

    # Test case: config.json
    # In gitignore: no mention of *.json
    # In customignore: *.json
    # Expected: excluded regardless of order
    assert rules1.exclude("config.json")
    assert rules2.exclude("config.json")

    # Test case: important.json
    # In gitignore: no mention of *.json
    # In customignore: *.json then !important.json
    # Expected: not excluded regardless of order
    assert not rules1.exclude("important.json")
    assert not rules2.exclude("important.json")


def test_load_rules_incrementally(temp_gitignore, temp_npmignore):
    """Test adding exclusion rules incrementally."""
    # Start with just gitignore
    rules = GitIgnoreExclusionRules(temp_gitignore)

    # Check initial state
    assert rules.exclude("file.txt")
    assert not rules.exclude("debug.log")  # Not excluded yet

    # Add npmignore rules
    rules.load_rules(temp_npmignore)

    # Now check again
    assert rules.exclude("file.txt")  # Still excluded
    assert rules.exclude("debug.log")  # Now excluded
    assert not rules.exclude("important.log")  # Negation works


def test_input_type_handling(temp_gitignore):
    """Test different input types for rules_files parameter."""
    # Test with string
    rules1 = GitIgnoreExclusionRules(temp_gitignore)
    assert rules1.exclude("file.txt")

    # Test with Path object
    rules2 = GitIgnoreExclusionRules(Path(temp_gitignore))
    assert rules2.exclude("file.txt")

    # Test with list containing one string
    rules3 = GitIgnoreExclusionRules([temp_gitignore])
    assert rules3.exclude("file.txt")

    # Test with None (should create empty rule set)
    rules4 = GitIgnoreExclusionRules(None)
    assert not rules4.exclude("file.txt")


def test_none_does_not_exclude():
    """Test that None parameter creates rules that don't exclude anything."""
    rules = GitIgnoreExclusionRules(None)
    assert not rules.exclude("anything.txt")
    assert not rules.exclude("file.py")
    assert not rules.exclude("node_modules/module.js")


def test_negation_override_across_files(temp_gitignore, temp_customignore):
    """Test complex overriding with negation patterns across multiple files."""
    # Create specific test files
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
        f1.write("*.md\n")  # Exclude all markdown files
        f1.write("!README.md\n")  # But keep README.md

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
        f2.write("README.md\n")  # Explicitly exclude README.md

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f3:
        f3.write("!README.md\n")  # Override to include README.md

    try:
        # Order matters: f1 then f2 should exclude README.md
        rules1 = GitIgnoreExclusionRules([f1.name, f2.name])
        assert rules1.exclude("README.md")
        assert rules1.exclude("CONTRIBUTING.md")

        # Order matters: f1 then f2 then f3 should include README.md again
        rules2 = GitIgnoreExclusionRules([f1.name, f2.name, f3.name])
        assert not rules2.exclude("README.md")
        assert rules2.exclude("CONTRIBUTING.md")
    finally:
        os.unlink(f1.name)
        os.unlink(f2.name)
        os.unlink(f3.name)


def test_empty_list_does_not_exclude():
    """Test that an empty list creates rules that don't exclude anything."""
    rules = GitIgnoreExclusionRules([])
    assert not rules.exclude("anything.txt")
    assert not rules.exclude("file.py")
