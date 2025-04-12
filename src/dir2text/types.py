from enum import Enum
from os import PathLike
from typing import Union

# Complete path type including strings and any path-like object
PathType = Union[str, PathLike[str]]


class FileType(Enum):
    """Enumeration of file types for categorizing items during traversal.

    This enum is used to differentiate between regular files, directories, and symlinks
    when processing the filesystem.

    Attributes:
        FILE: Regular file
        DIRECTORY: Directory
        SYMLINK: Symbolic link
    """

    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
