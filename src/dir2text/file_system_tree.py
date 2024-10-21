import os
from typing import Iterator, Optional, Tuple

from anytree import Node

from dir2text.exclusion_rules.base_rules import BaseExclusionRules


class FileSystemNode(Node):
    def __init__(self, name, parent=None, is_dir=False, **kwargs):
        super().__init__(name, parent, **kwargs)
        self.is_dir = is_dir


class FileSystemTree:
    def __init__(self, root_path: str, exclusion_rules: Optional[BaseExclusionRules] = None):
        self.root_path = os.path.abspath(root_path)
        self.exclusion_rules = exclusion_rules
        self._tree: Optional[FileSystemNode] = None
        self._file_count: int = 0
        self._directory_count: int = 0

    def get_tree(self) -> Optional[FileSystemNode]:
        if self._tree is None:
            self._build_tree()
        return self._tree

    def _build_tree(self):
        if not os.path.exists(self.root_path):
            raise FileNotFoundError(f"Root path does not exist: {self.root_path}")
        if not os.path.isdir(self.root_path):
            raise NotADirectoryError(f"Root path is not a directory: {self.root_path}")
        self._tree = self._create_node(self.root_path, "")
        self._count_files_and_directories()

    def _create_node(
        self, path: str, relative_path: str, parent: Optional[FileSystemNode] = None
    ) -> Optional[FileSystemNode]:
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
            except PermissionError:
                pass
        return node

    def _count_files_and_directories(self):
        self._file_count = 0
        self._directory_count = 0

        def count(node: FileSystemNode):
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
        """
        Returns the number of files in the tree, respecting exclusion rules.
        """
        if self._tree is None:
            self._build_tree()
        return self._file_count

    def get_directory_count(self) -> int:
        """
        Returns the number of directories in the tree (excluding the root), respecting exclusion rules.
        """
        if self._tree is None:
            self._build_tree()
        return self._directory_count

    def iterate_files(self) -> Iterator[Tuple[str, str]]:
        """
        Yields tuples of (file_path, relative_path) for all files in the tree.
        """
        if self._tree is None:
            self._build_tree()

        if self._tree is not None:
            yield from self._iterate(self._tree, "")

    def _iterate(self, node: FileSystemNode, current_path: str) -> Iterator[Tuple[str, str]]:
        if not node.is_dir:
            yield (os.path.join(self.root_path, current_path), current_path)
        else:
            for child in node.children:
                yield from self._iterate(child, os.path.join(current_path, child.name))

    def get_tree_representation(self) -> str:
        if self._tree is None:
            self._build_tree()
        if self._tree is None:  # If the root is excluded
            return ""

        output = []

        def write_node(node: FileSystemNode, prefix: str = "", is_last: bool = True):
            if not node.parent:  # Root node
                output.append(f"{node.name}/")
            else:
                connector = "└── " if is_last else "├── "
                output.append(f"{prefix}{connector}{node.name}{'/' if node.is_dir else ''}")

            if node.children:
                new_prefix = prefix + ("    " if is_last else "│   ")
                # Sort children: directories first, then files, both alphabetically
                sorted_children = sorted(node.children, key=lambda n: (not n.is_dir, n.name.lower()))
                for i, child in enumerate(sorted_children):
                    is_last_child = i == len(sorted_children) - 1
                    write_node(child, new_prefix, is_last_child)

        write_node(self._tree)
        return "\n".join(output)

    def refresh(self):
        self._tree = None
        self._file_count = 0
        self._directory_count = 0
        self._build_tree()
