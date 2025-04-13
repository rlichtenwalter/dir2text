"""Unit tests for the FileSystemTree class."""

import os
from pathlib import Path

import pytest

from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.file_system_tree.file_system_tree import FileSystemTree


@pytest.fixture
def temp_directory(tmp_path):
    # Create a temporary directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").touch()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.py").touch()
    (tmp_path / "dir2" / "file2.pyc").touch()
    return tmp_path


@pytest.fixture
def temp_directory_with_symlinks(tmp_path):
    """Create a temporary directory structure with symlinks."""
    # Create directories and files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass")
    (tmp_path / "src" / "utils").mkdir()
    (tmp_path / "src" / "utils" / "helpers.py").write_text("def helper(): pass")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("# Documentation")

    # Create symlinks
    try:
        # Create a symlink from "build" to "src"
        os.symlink(tmp_path / "src", tmp_path / "build")

        # Create a symlink loop
        os.symlink(tmp_path / "src", tmp_path / "src" / "utils" / "loop")

        has_symlinks = True
    except (OSError, NotImplementedError):
        # On some platforms (like Windows) creating symlinks might require special permissions
        has_symlinks = False

    return tmp_path, has_symlinks


@pytest.fixture
def temp_gitignore(temp_directory):
    gitignore_content = "*.pyc"
    gitignore_file = temp_directory / ".gitignore"
    gitignore_file.write_text(gitignore_content)
    return str(gitignore_file)


def test_file_system_tree_initialization(temp_directory):
    fs_tree = FileSystemTree(str(temp_directory))
    assert fs_tree.root_path == Path(temp_directory)
    assert fs_tree._tree is None


def test_file_system_tree_build(temp_directory):
    fs_tree = FileSystemTree(str(temp_directory))
    tree = fs_tree.get_tree()
    assert tree is not None
    assert tree.name == temp_directory.name
    assert tree.children is not None
    assert len(tree.children) == 2  # dir1 and dir2


def test_file_system_tree_with_exclusions(temp_directory, temp_gitignore):
    exclusion_rules = GitIgnoreExclusionRules(temp_gitignore)
    fs_tree = FileSystemTree(str(temp_directory), exclusion_rules)
    tree = fs_tree.get_tree()
    assert tree is not None
    assert tree.children is not None
    dir2 = next((node for node in tree.children if node.name == "dir2"), None)
    assert dir2 is not None
    assert dir2.children is not None
    assert len(dir2.children) == 1  # Only file2.py, file2.pyc is excluded


def test_file_system_tree_refresh(temp_directory):
    fs_tree = FileSystemTree(str(temp_directory))
    fs_tree.get_tree()
    (temp_directory / "new_file.txt").touch()
    fs_tree.refresh()
    tree = fs_tree.get_tree()
    assert tree is not None
    assert tree.children is not None
    assert any(node.name == "new_file.txt" for node in tree.children)


def test_file_system_tree_non_existent_directory():
    with pytest.raises(FileNotFoundError):
        FileSystemTree("/non/existent/directory").get_tree()


def test_file_system_tree_file_as_root():
    with pytest.raises(NotADirectoryError):
        FileSystemTree(__file__).get_tree()


def test_file_system_tree_empty_directory(temp_directory):
    # Test handling of empty directories
    empty_dir = temp_directory / "empty_dir"
    empty_dir.mkdir()
    fs_tree = FileSystemTree(str(temp_directory))
    tree = fs_tree.get_tree()
    empty_node = next((node for node in tree.children if node.name == "empty_dir"), None)
    assert empty_node is not None
    assert empty_node.children == ()


def test_symlink_detection(temp_directory_with_symlinks):
    """Test that symlinks are properly detected and represented."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Test with default behavior (don't follow symlinks)
    fs_tree = FileSystemTree(str(tmp_path))
    tree = fs_tree.get_tree()

    # Get the build symlink node
    build_node = next((node for node in tree.children if node.name == "build"), None)
    assert build_node is not None
    assert build_node.is_symlink
    assert build_node.symlink_target is not None

    # Check symlink count
    assert fs_tree.get_symlink_count() == 2

    # Check tree representation
    tree_repr = fs_tree.get_tree_representation()
    assert "build → " in tree_repr
    assert "[symlink]" in tree_repr

    # Check symlink iteration
    symlinks = list(fs_tree.iterate_symlinks())
    assert len(symlinks) == 2
    symlink_paths = [s[1] for s in symlinks]  # Get relative paths
    assert "build" in symlink_paths


def test_follow_symlinks(temp_directory_with_symlinks):
    """Test following symlinks during traversal."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Test with follow_symlinks=True
    fs_tree = FileSystemTree(str(tmp_path), follow_symlinks=True)
    tree = fs_tree.get_tree()

    # Now build should be treated as a directory, not a symlink
    build_node = next((node for node in tree.children if node.name == "build"), None)
    assert build_node is not None
    assert build_node.is_dir
    assert not build_node.is_symlink

    # Check that the contents of the src directory are also under build
    assert any(node.name == "main.py" for node in build_node.children)

    # Check symlink count - should be 0 since we're following symlinks
    assert fs_tree.get_symlink_count() == 0

    # Check tree representation
    tree_repr = fs_tree.get_tree_representation()
    assert "build/" in tree_repr  # Should be shown as directory
    assert "loop/" not in tree_repr  # Loop should be detected and not followed

    # Check file iteration to verify we can access the files through symlinks
    files = list(fs_tree.iterate_files())
    file_paths = [f[1] for f in files]  # Get relative paths

    # We should have these files:
    # - src/main.py
    # - src/utils/helpers.py
    # - docs/readme.md
    # - build/main.py (same file as src/main.py)
    # - build/utils/helpers.py (same file as src/utils/helpers.py)
    assert len(files) == 5
    assert "src/main.py" in file_paths
    assert "build/main.py" in file_paths


def test_symlink_loop_detection(temp_directory_with_symlinks):
    """Test that symlink loops are properly detected and handled."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Create a tree with follow_symlinks=True
    fs_tree = FileSystemTree(str(tmp_path), follow_symlinks=True)

    # Get the tree (this should not hang due to loop detection)
    tree = fs_tree.get_tree()

    # Verify the loop is detected by checking tree structure
    # Find the loop node (utils/loop)
    loop_node = None
    for node in tree.descendants:
        if node.name == "loop" and hasattr(node, "symlink_target"):
            loop_node = node
            break

    # Assert that we found the loop node and it's properly marked
    assert loop_node is not None
    assert loop_node.is_symlink
    assert hasattr(loop_node, "symlink_target")
    assert "loop" in loop_node.symlink_target or "[loop detected]" == loop_node.symlink_target


def test_iterate_symlinks(temp_directory_with_symlinks):
    """Test iterate_symlinks method."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Create tree with default settings (don't follow symlinks)
    fs_tree = FileSystemTree(str(tmp_path))

    # Iterate symlinks
    symlinks = list(fs_tree.iterate_symlinks())
    assert len(symlinks) == 2

    # Check format of symlink tuples: (abs_path, rel_path, target)
    for symlink in symlinks:
        assert len(symlink) == 3
        abs_path, rel_path, target = symlink
        assert os.path.isabs(abs_path)
        assert not os.path.isabs(rel_path)
        assert target  # Should have a target string

    # With follow_symlinks=True, iterate_symlinks should return empty
    fs_tree_follow = FileSystemTree(str(tmp_path), follow_symlinks=True)
    symlinks_follow = list(fs_tree_follow.iterate_symlinks())
    assert len(symlinks_follow) == 0


def test_symlinks_with_exclusions(temp_directory_with_symlinks):
    """Test combining symlink handling with exclusion rules."""
    tmp_path, has_symlinks = temp_directory_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Create a temporary exclusion file
    exclusion_file = tmp_path / ".dir2textignore"
    exclusion_file.write_text("build/\n*.md\n")

    # Create exclusion rules
    rules = GitIgnoreExclusionRules(exclusion_file)

    # Create a tree with exclusions
    fs_tree = FileSystemTree(str(tmp_path), exclusion_rules=rules)

    # Check that excluded symlinks aren't in the tree
    tree = fs_tree.get_tree()
    build_node = next((node for node in tree.children if node.name == "build"), None)
    assert build_node is None  # Should be excluded

    # Check that excluded files aren't in the iteration
    files = list(fs_tree.iterate_files())
    file_paths = [f[1] for f in files]

    assert "docs/readme.md" not in file_paths  # Should be excluded
    assert "src/main.py" in file_paths  # Should be included
    assert "src/utils/helpers.py" in file_paths  # Should be included

    # Check symlinks - build should be excluded
    symlinks = list(fs_tree.iterate_symlinks())
    symlink_paths = [s[1] for s in symlinks]
    assert "build" not in symlink_paths
    assert "src/utils/loop" in symlink_paths  # Still included
