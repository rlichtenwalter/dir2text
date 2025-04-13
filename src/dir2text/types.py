from os import PathLike
from typing import Union

# Complete path type including strings and any path-like object
PathType = Union[str, PathLike[str]]
