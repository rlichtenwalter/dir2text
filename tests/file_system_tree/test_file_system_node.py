"""Unit tests for the FileSystemNode class."""

from dir2text.file_system_tree.file_system_node import FileSystemNode


def test_file_system_node_initialization():
    """Test basic initialization of FileSystemNode."""
    # Test file node
    file_node = FileSystemNode("test_file.txt", is_dir=False)
    assert file_node.name == "test_file.txt"
    assert not file_node.is_dir
    assert not file_node.is_symlink
    assert file_node.symlink_target is None

    # Test directory node
    dir_node = FileSystemNode("test_dir", is_dir=True)
    assert dir_node.name == "test_dir"
    assert dir_node.is_dir
    assert not dir_node.is_symlink
    assert dir_node.symlink_target is None

    # Test symlink node
    symlink_node = FileSystemNode("test_link", is_symlink=True, symlink_target="./target.txt")
    assert symlink_node.name == "test_link"
    assert not symlink_node.is_dir
    assert symlink_node.is_symlink
    assert symlink_node.symlink_target == "./target.txt"


def test_file_system_node_parent_child():
    """Test parent-child relationships in FileSystemNode."""
    # Create a simple tree
    root = FileSystemNode("root", is_dir=True)
    child1 = FileSystemNode("child1", parent=root, is_dir=True)
    child2 = FileSystemNode("child2", parent=root, is_dir=False)
    grandchild = FileSystemNode("grandchild", parent=child1, is_dir=False)

    # Test parent relationships
    assert child1.parent == root
    assert child2.parent == root
    assert grandchild.parent == child1
    assert root.parent is None

    # Test children
    assert len(root.children) == 2
    assert child1 in root.children
    assert child2 in root.children
    assert len(child1.children) == 1
    assert grandchild in child1.children
    assert len(child2.children) == 0


def test_file_system_node_with_additional_attributes():
    """Test FileSystemNode with additional attributes."""
    # Create a node with extra attributes
    node = FileSystemNode("test_file.txt", is_dir=False, size=1024, modified_time="2023-01-01")

    # Test that additional attributes were stored
    assert node.name == "test_file.txt"
    assert not node.is_dir
    assert hasattr(node, "size")
    assert node.size == 1024
    assert hasattr(node, "modified_time")
    assert node.modified_time == "2023-01-01"
