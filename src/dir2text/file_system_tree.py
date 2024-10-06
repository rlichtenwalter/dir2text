import os
from io import StringIO
from typing import Optional, List
from anytree import Node
from .exclusion_rules import ExclusionRules


class FileSystemTree:
    def __init__(self, root_path: str, exclusion_rules: Optional[ExclusionRules] = None):
        self.root_path = os.path.abspath(root_path)
        self.exclusion_rules = exclusion_rules
        self._tree: Optional[Node] = None

    def get_tree(self) -> Node:
        if self._tree is None:
            self._build_tree()
        return self._tree

    def _build_tree(self):
        if not os.path.exists(self.root_path):
            raise FileNotFoundError(f"Root path does not exist: {self.root_path}")
        if not os.path.isdir(self.root_path):
            raise NotADirectoryError(f"Root path is not a directory: {self.root_path}")

        self._tree = self._create_node(self.root_path)

    def _create_node(self, path: str, parent: Optional[Node] = None) -> Node:
        name = os.path.basename(path)
        node = Node(name, parent=parent)

        if os.path.isdir(path):
            try:
                for child in os.listdir(path):
                    child_path = os.path.join(path, child)
                    if self.exclusion_rules and self.exclusion_rules.exclude(child_path):
                        continue
                    self._create_node(child_path, parent=node)
            except PermissionError:
                print(f"Permission denied: {path}")

        return node

    def refresh(self):
        self._tree = None
        self._build_tree()

    def get_tree_representation(self) -> str:
        if self._tree is None:
            self._build_tree()

        output = StringIO()

        def sort_key(node: Node) -> tuple:
            return (not node.is_leaf, node.name.lower())

        def write_node(node: Node, prefix: str, is_last: bool, ancestors_last: List[bool]):
            if len(ancestors_last) > 1:
                for is_last_ancestor in ancestors_last[1:-1]:
                    output.write("│   " if not is_last_ancestor else "    ")

            if len(ancestors_last) > 0:
                output.write("└── " if is_last else "├── ")

            output.write(f"{node.name}{'/' if not node.is_leaf else ''}\n")

            children = sorted(node.children, key=sort_key)
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                write_node(child, prefix + "    ", is_last_child, ancestors_last + [is_last])

        output.write(f"{self._tree.name}/\n")
        children = sorted(self._tree.children, key=sort_key)
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            write_node(child, "", is_last, [is_last])

        return output.getvalue()
