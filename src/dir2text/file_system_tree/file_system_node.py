"""Node representation for file system elements in the tree."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from anytree import Node


class FileSystemNode(Node):
    """Node class representing a file or directory in the filesystem tree.

    Extends anytree.Node to add flags indicating whether the node represents
    a directory, a symlink, or other file types. Inherits tree traversal and
    manipulation capabilities from anytree.Node.

    Attributes:
        name (str): The name of the file or directory (just the basename).
        parent (Optional[FileSystemNode]): The parent node in the tree.
        is_dir (bool): True if this node represents a directory, False for files.
        is_symlink (bool): True if this node represents a symbolic link.
        symlink_target (Optional[str]): Target path of the symlink, if this is a symlink.
        children (tuple[FileSystemNode, ...]): The child nodes (inherited from anytree.Node).

    Example:
        >>> root = FileSystemNode("root", is_dir=True)
        >>> child = FileSystemNode("file.txt", parent=root, is_dir=False)
        >>> root.name
        'root'
        >>> child.is_dir
        False
    """

    children: tuple[FileSystemNode, ...]  # type: ignore[assignment]
    is_dir: bool
    is_symlink: bool
    symlink_target: str | None

    def __init__(
        self,
        name: str,
        parent: FileSystemNode | None = None,
        is_dir: bool = False,
        is_symlink: bool = False,
        symlink_target: str | None = None,
        children: Iterable[FileSystemNode] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a FileSystemNode.

        Args:
            name: The name of the file or directory.
            parent: The parent node. Defaults to None.
            is_dir: Whether this node represents a directory. Defaults to False.
            is_symlink: Whether this node represents a symbolic link. Defaults to False.
            symlink_target: The target path of the symlink. Only applicable if is_symlink is True.
            children: Child nodes. Defaults to None.
            **kwargs: Additional arguments passed to anytree.Node.

        Example:
            >>> node = FileSystemNode("example.txt", is_dir=False)
            >>> node.name
            'example.txt'
            >>> node.is_dir
            False
        """
        super().__init__(name, parent, children=children, **kwargs)
        self.is_dir = is_dir
        self.is_symlink = is_symlink
        self.symlink_target = symlink_target
