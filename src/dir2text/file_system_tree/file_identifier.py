"""File identifier for uniquely identifying files by device and inode."""

from typing import Any


class FileIdentifier:
    """Class for uniquely identifying files and directories by their device and inode.

    This class is used for tracking unique files during traversal, particularly for
    symlink loop detection. The combination of device ID and inode number uniquely
    identifies a file or directory in the filesystem.

    Attributes:
        device_id (int): The device ID from stat information.
        inode_number (int): The inode number from stat information.

    Note:
        On Windows, inode numbers might be handled differently than on Unix systems,
        but Python's os.stat implementation provides values that can be used
        for uniquely identifying files.
    """

    def __init__(self, device_id: int, inode_number: int):
        """Initialize a FileIdentifier.

        Args:
            device_id: The device ID from stat information.
            inode_number: The inode number from stat information.
        """
        self.device_id = device_id
        self.inode_number = inode_number

    def __eq__(self, other: Any) -> bool:
        """Check equality with another FileIdentifier.

        Args:
            other: Another object to compare with.

        Returns:
            True if the other object is a FileIdentifier with the same
            device_id and inode_number.
        """
        if not isinstance(other, FileIdentifier):
            return False
        return self.device_id == other.device_id and self.inode_number == other.inode_number

    def __hash__(self) -> int:
        """Generate a hash value for use in dictionaries and sets.

        Returns:
            A hash based on device_id and inode_number.
        """
        return hash((self.device_id, self.inode_number))

    def __repr__(self) -> str:
        """Create a string representation of the FileIdentifier.

        Returns:
            A string representation showing device_id and inode_number.
        """
        return f"FileIdentifier(device_id={self.device_id}, inode_number={self.inode_number})"
