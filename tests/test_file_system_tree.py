import os
from pathlib import Path

import pytest

from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.file_system_tree import FileSystemTree


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


def test_file_system_tree_symlinks(temp_directory):
    # Test handling of symbolic links
    target_file = temp_directory / "target.txt"
    target_file.touch()
    symlink = temp_directory / "link.txt"
    try:
        symlink.symlink_to(target_file)
        fs_tree = FileSystemTree(str(temp_directory))
        tree = fs_tree.get_tree()
        assert any(node.name == "link.txt" for node in tree.children)
    except OSError:  # Handles cases where symlink creation requires privileges
        pytest.skip("Symbolic link creation not supported")


def test_file_system_tree_special_chars(temp_directory):
    # Test handling of special characters in file names
    special_names = [
        "file with spaces.txt",
        "file_with_उनिकोड.txt",
        "!special!.txt",
        "#hashtag.txt",
        "file.with.dots.txt",
        "-leading-dash.txt",
        ".hidden_file",
    ]

    for name in special_names:
        (temp_directory / name).touch()

    fs_tree = FileSystemTree(str(temp_directory))
    tree = fs_tree.get_tree()

    for name in special_names:
        assert any(node.name == name for node in tree.children)


def test_file_system_tree_deep_recursion(temp_directory):
    # Test handling of deeply nested directories
    current = temp_directory
    depth = 50  # Deep enough to test recursion but not too deep to cause issues

    for i in range(depth):
        current = current / f"dir_{i}"
        current.mkdir()
        (current / f"file_{i}.txt").touch()

    fs_tree = FileSystemTree(str(temp_directory))
    tree = fs_tree.get_tree()

    # Verify we can traverse to the deepest level
    current_node = tree
    for i in range(depth):
        current_node = next((node for node in current_node.children if node.name == f"dir_{i}"), None)
        assert current_node is not None
        assert any(node.name == f"file_{i}.txt" for node in current_node.children)


def test_file_system_tree_permission_denied(temp_directory):
    # Test handling of permission-denied directories
    restricted_dir = temp_directory / "restricted"
    restricted_dir.mkdir()
    (restricted_dir / "file.txt").touch()

    try:
        os.chmod(restricted_dir, 0o000)  # Remove all permissions
        fs_tree = FileSystemTree(str(temp_directory))
        tree = fs_tree.get_tree()
        # Should still see the directory but might not access its contents
        assert any(node.name == "restricted" for node in tree.children)
    except OSError:  # Handles cases where permission changes require privileges
        pytest.skip("Permission modification not supported")
    finally:
        os.chmod(restricted_dir, 0o755)  # Restore permissions for cleanup


def test_file_system_tree_zero_byte_files(temp_directory):
    # Test handling of zero-byte files
    zero_byte_file = temp_directory / "empty.txt"
    zero_byte_file.touch()

    fs_tree = FileSystemTree(str(temp_directory))
    tree = fs_tree.get_tree()
    assert any(node.name == "empty.txt" for node in tree.children)
