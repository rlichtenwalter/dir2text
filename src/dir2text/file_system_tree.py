"""File system tree representation with configurable exclusion rules.

This module provides classes for building and manipulating tree representations of
directory structures, with support for excluding files and directories based on
specified rules.
"""

import os
from enum import Enum
from typing import Any, Iterator, Optional, Tuple

from anytree import Node

from dir2text.exclusion_rules.base_rules import BaseExclusionRules


class PermissionAction(str, Enum):
    """Action to take when encountering permission errors during directory traversal.

    Values:
        IGNORE: Continue traversal silently, skipping inaccessible items (default behavior)
        RAISE: Raise a PermissionError immediately when access is denied
    """

    IGNORE = "ignore"
    RAISE = "raise"


class FileSystemNode(Node):  # type: ignore
    """Node class representing a file or directory in the filesystem tree.

    Extends anytree.Node to add a flag indicating whether the node represents
    a directory. Inherits all tree traversal and manipulation capabilities
    from anytree.Node.

    Attributes:
        name (str): The name of the file or directory (just the basename).
        parent (Optional[FileSystemNode]): The parent node in the tree.
        is_dir (bool): True if this node represents a directory, False for files.
        children (tuple[FileSystemNode]): The child nodes (inherited from anytree.Node).

    Example:
        >>> root = FileSystemNode("root", is_dir=True)
        >>> child = FileSystemNode("file.txt", parent=root, is_dir=False)
        >>> root.name
        'root'
        >>> child.is_dir
        False
    """

    def __init__(
        self, name: str, parent: Optional["FileSystemNode"] = None, is_dir: bool = False, **kwargs: Any
    ) -> None:
        """Initialize a FileSystemNode.

        Args:
            name: The name of the file or directory.
            parent: The parent node. Defaults to None.
            is_dir: Whether this node represents a directory. Defaults to False.
            **kwargs: Additional arguments passed to anytree.Node.

        Example:
            >>> node = FileSystemNode("example.txt", is_dir=False)
            >>> node.name
            'example.txt'
            >>> node.is_dir
            False
        """
        super().__init__(name, parent, **kwargs)
        self.is_dir = is_dir


class FileSystemTree:
    """A tree representation of a directory structure with support for exclusion rules.

    This class builds and maintains a tree representation of a directory structure,
    optionally filtering files and directories based on provided exclusion rules.
    It supports lazy tree building, directory/file counting, and both streaming and
    complete tree representations.

    The tree is built lazily on first access and can be refreshed to reflect filesystem
    changes. Both full tree access and iterative file listing are supported.

    Symbolic Link Behavior:
        The current implementation follows symbolic links during traversal without
        detecting or preventing symlink loops. Users should be cautious when processing
        directories containing circular symbolic links, as this could lead to infinite
        recursion. Future versions may add configuration options for controlling
        symlink handling.

    Permission Handling:
        Permission errors during traversal can be handled in two ways:
        - IGNORE (default): Silently skip inaccessible files/directories
        - RAISE: Immediately raise PermissionError when access is denied

    Attributes:
        root_path (str): The absolute path to the root directory.
        exclusion_rules (Optional[BaseExclusionRules]): Rules for excluding files/directories.
        permission_action (PermissionAction): How to handle permission errors.

    Example:
        >>> # Create a tree for the current directory without exclusions
        >>> tree = FileSystemTree(".")  # doctest: +SKIP
        >>> # Print the complete tree
        >>> print(tree.get_tree_representation())  # doctest: +SKIP
        .
        ├── file1.txt
        └── subdir/
            └── file2.txt
    """

    def __init__(
        self,
        root_path: str,
        exclusion_rules: Optional[BaseExclusionRules] = None,
        permission_action: PermissionAction = PermissionAction.IGNORE,
    ) -> None:
        """Initialize a FileSystemTree.

        Args:
            root_path: Path to the root directory to represent.
            exclusion_rules: Rules for excluding files and directories. Defaults to None.
            permission_action: How to handle permission errors during traversal.
                Defaults to IGNORE.

        Example:
            >>> tree = FileSystemTree(".")  # doctest: +SKIP
            >>> # Access causes lazy tree building
            >>> tree.get_file_count()  # doctest: +SKIP
            42
        """
        self.root_path = os.path.abspath(root_path)
        self.exclusion_rules = exclusion_rules
        self.permission_action = permission_action
        self._tree: Optional[FileSystemNode] = None
        self._file_count: int = 0
        self._directory_count: int = 0

    def get_tree(self) -> Optional[FileSystemNode]:
        """Get the root node of the filesystem tree.

        Builds the tree if it hasn't been built yet. The tree is built lazily on first
        access to avoid unnecessary filesystem operations.

        Returns:
            The root node of the tree, or None if the tree couldn't be built.

        Raises:
            FileNotFoundError: If the root path doesn't exist.
            NotADirectoryError: If the root path isn't a directory.
            PermissionError: If permission is denied and permission_action is RAISE.

        Example:
            >>> tree = FileSystemTree(".")  # doctest: +SKIP
            >>> root = tree.get_tree()  # doctest: +SKIP
            >>> root.name  # doctest: +SKIP
            '.'
        """
        if self._tree is None:
            self._build_tree()
        return self._tree

    def _build_tree(self) -> None:
        """Build the filesystem tree from the root path.

        Creates a tree representation of the filesystem starting at root_path,
        respecting any configured exclusion rules. Also counts the total number
        of files and directories.

        Raises:
            FileNotFoundError: If the root path doesn't exist.
            NotADirectoryError: If the root path isn't a directory.
            PermissionError: If permission is denied and permission_action is RAISE.
        """
        if not os.path.exists(self.root_path):
            raise FileNotFoundError(f"Root path does not exist: {self.root_path}")
        if not os.path.isdir(self.root_path):
            raise NotADirectoryError(f"Root path is not a directory: {self.root_path}")
        self._tree = self._create_node(self.root_path, "")
        self._count_files_and_directories()

    def _create_node(
        self, path: str, relative_path: str, parent: Optional[FileSystemNode] = None
    ) -> Optional[FileSystemNode]:
        """Recursively create tree nodes for a path and its children.

        Args:
            path: Absolute path to create node for.
            relative_path: Path relative to root_path, used for exclusion checking.
            parent: Parent node. Defaults to None.

        Returns:
            The created node, or None if the path should be excluded.

        Raises:
            PermissionError: If access is denied and permission_action is RAISE.
        """
        name = os.path.basename(path)
        if self.exclusion_rules and self.exclusion_rules.exclude(relative_path):
            return None

        is_dir = os.path.isdir(path)
        node = FileSystemNode(name, parent=parent, is_dir=is_dir)

        if is_dir:
            try:
                for child in sorted(os.listdir(path)):
                    child_path = os.path.join(path, child)
                    child_relative_path = os.path.join(relative_path, child).replace("\\", "/")
                    child_node = self._create_node(child_path, child_relative_path, parent=node)
                    if child_node is None:
                        node.children = [c for c in node.children if c is not child_node]
            except PermissionError as e:
                if self.permission_action == PermissionAction.RAISE:
                    raise PermissionError(f"Access denied to {path}: {e}")
                # For IGNORE, we keep the directory node but skip its contents
        return node

    def _count_files_and_directories(self) -> None:
        """Count the total number of files and directories in the tree.

        Updates _file_count and _directory_count based on the current tree.
        The root directory is not included in the directory count.
        """
        self._file_count = 0
        self._directory_count = 0

        def count(node: FileSystemNode) -> None:
            if node.is_dir:
                self._directory_count += 1
                for child in node.children:
                    count(child)
            else:
                self._file_count += 1

        if self._tree:
            count(self._tree)
        self._directory_count -= 1  # Subtract 1 to exclude the root directory from the count

    def get_file_count(self) -> int:
        """Get the total number of files in the tree.

        Returns:
            Number of files (excluding those filtered by exclusion rules).

        Example:
            >>> tree = FileSystemTree(".")  # doctest: +SKIP
            >>> tree.get_file_count()  # doctest: +SKIP
            42
        """
        if self._tree is None:
            self._build_tree()
        return self._file_count

    def get_directory_count(self) -> int:
        """Get the total number of directories in the tree (excluding root).

        Returns:
            Number of directories (excluding root and those filtered by exclusion rules).

        Example:
            >>> tree = FileSystemTree(".")  # doctest: +SKIP
            >>> tree.get_directory_count()  # doctest: +SKIP
            5
        """
        if self._tree is None:
            self._build_tree()
        return self._directory_count

    def iterate_files(self) -> Iterator[Tuple[str, str]]:
        """Iterate over all files in the tree.

        Yields each file's absolute path and path relative to the root directory.
        Files are yielded in sorted order (by directory, then filename).

        Yields:
            Pairs of (absolute_path, relative_path) for each file.

        Raises:
            PermissionError: If access is denied and permission_action is RAISE.

        Example:
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> for abs_path, rel_path in tree.iterate_files():  # doctest: +SKIP
            ...     print(f"{rel_path}")
            main.py
            utils/helpers.py
        """
        if self._tree is None:
            self._build_tree()

        if self._tree is not None:
            yield from self._iterate(self._tree, "")

    def _iterate(self, node: FileSystemNode, current_path: str) -> Iterator[Tuple[str, str]]:
        """Recursive helper for iterate_files.

        Args:
            node: Current node to process.
            current_path: Path to the current node relative to root.

        Yields:
            Pairs of (absolute_path, relative_path) for each file.
        """
        if not node.is_dir:
            yield (os.path.join(self.root_path, current_path), current_path)
        else:
            for child in node.children:
                yield from self._iterate(child, os.path.join(current_path, child.name))

    def stream_tree_representation(self) -> Iterator[str]:
        """Generate a tree representation of the filesystem one line at a time.

        Generates output similar to the Unix 'tree' command, with files and directories
        shown in a hierarchical structure using ASCII characters.

        Yields:
            Lines of the tree representation, including the connecting lines.

        Raises:
            PermissionError: If access is denied and permission_action is RAISE.

        Example:
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> for line in tree.stream_tree_representation():  # doctest: +SKIP
            ...     print(line)
            src/
            ├── main.py
            └── utils/
                └── helpers.py
        """
        if self._tree is None:
            self._build_tree()
        if self._tree is None:
            return

        def write_node(node: FileSystemNode, prefix: str = "", is_last: bool = True) -> Iterator[str]:
            # Handle root node
            if not node.parent:
                yield f"{node.name}/"
            else:
                # Handle child nodes
                connector = "└── " if is_last else "├── "
                yield f"{prefix}{connector}{node.name}{'/' if node.is_dir else ''}"

            if node.children:
                new_prefix = prefix + ("    " if is_last else "│   ")
                # Sort children: directories first, then files, both alphabetically
                sorted_children = sorted(node.children, key=lambda n: (not n.is_dir, n.name.lower()))

                # Process each child
                for i, child in enumerate(sorted_children):
                    is_last_child = i == len(sorted_children) - 1
                    yield from write_node(child, new_prefix, is_last_child)

        yield from write_node(self._tree)

    def get_tree_representation(self) -> str:
        """Get a complete string representation of the filesystem tree.

        Returns:
            The complete tree representation as a string.

        Raises:
            PermissionError: If access is denied and permission_action is RAISE.

        Example:
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> print(tree.get_tree_representation())  # doctest: +SKIP
            src/
            ├── main.py
            └── utils/
                └── helpers.py
        """
        return "\n".join(self.stream_tree_representation())

    def refresh(self) -> None:
        """Refresh the tree to reflect current filesystem state.

        Clears the cached tree and counts, forcing a rebuild on next access.
        Use this method if the filesystem has changed and you need up-to-date
        information.

        Example:
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> tree.get_file_count()  # doctest: +SKIP
            5
            >>> # ... files added to src/ ...
            >>> tree = FileSystemTree("src")  # doctest: +SKIP
            >>> tree.refresh()  # doctest: +SKIP
            >>> tree.get_file_count()  # doctest: +SKIP
            6
        """
        self._tree = None
        self._file_count = 0
        self._directory_count = 0
        self._build_tree()
