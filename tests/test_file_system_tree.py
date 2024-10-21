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
    assert fs_tree.root_path == str(temp_directory)
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
