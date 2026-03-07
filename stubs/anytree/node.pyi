from collections.abc import Iterable
from typing import Any

class Node:
    separator: str
    name: str
    parent: Node | None
    children: tuple[Node, ...]
    depth: int
    height: int
    is_leaf: bool
    is_root: bool
    root: Node
    ancestors: tuple[Node, ...]
    descendants: tuple[Node, ...]
    leaves: tuple[Node, ...]
    siblings: tuple[Node, ...]
    path: tuple[Node, ...]
    size: int

    def __init__(
        self,
        name: str,
        parent: Node | None = None,
        children: Iterable[Node] | None = None,
        **kwargs: Any,
    ) -> None: ...
