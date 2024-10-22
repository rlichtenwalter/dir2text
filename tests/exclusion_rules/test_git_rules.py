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
