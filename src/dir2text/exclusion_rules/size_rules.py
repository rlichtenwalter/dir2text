"""Size-based exclusion rules for filtering files by size."""

from pathlib import Path
from typing import Union

from .base_rules import BaseExclusionRules


def parse_file_size(size_str: str) -> int:
    """Parse human-readable file size to bytes.

    Args:
        size_str: Size string like '1GB', '500MB', '2.5K', or just '1024'

    Returns:
        Size in bytes

    Raises:
        ValueError: If size_str is not a valid size format
        ImportError: If humanfriendly library is not available
    """
    try:
        from humanfriendly import parse_size
    except ImportError:
        raise ImportError("humanfriendly is required for size parsing. " "Install it with: pip install humanfriendly")

    try:
        return int(parse_size(size_str))
    except Exception as e:
        raise ValueError(f"Invalid size format '{size_str}': {e}")


class SizeExclusionRules(BaseExclusionRules):
    """Exclusion rules based on file size limits.

    This class implements file size-based exclusion, where files exceeding
    a specified size limit are excluded from processing. The size limit can
    be specified in human-readable format (e.g., '1GB', '500MB') or as raw bytes.

    For symbolic links, the behavior depends on whether the symlink target
    should be followed:
    - By default, checks the target file size (more meaningful for content filtering)
    - The symlink file itself is typically very small (just the path to target)

    Attributes:
        max_size_bytes (int): Maximum allowed file size in bytes.

    Example:
        >>> # Create size-based exclusion rules
        >>> rules = SizeExclusionRules("1MB")  # 1 megabyte limit
        >>> rules.max_size_bytes  # Check the configured limit
        1000000
        >>> rules.has_rules()  # Check if rules are configured
        True
    """

    def __init__(self, max_size: Union[str, int]):
        """Initialize size exclusion rules.

        Args:
            max_size: Maximum file size. Can be:
                - String in human-readable format ('1GB', '500MB', '2.5K')
                - Integer representing bytes

        Raises:
            ValueError: If max_size format is invalid
            ImportError: If humanfriendly library is not available
        """
        if isinstance(max_size, str):
            self.max_size_bytes = parse_file_size(max_size)
        elif isinstance(max_size, int):
            if max_size < 0:
                raise ValueError("Size cannot be negative")
            self.max_size_bytes = max_size
        else:
            raise ValueError(f"max_size must be string or int, got {type(max_size)}")

    def exclude(self, path: str) -> bool:
        """Check if a file should be excluded based on size.

        Args:
            path: File path to check (can be relative or absolute).

        Returns:
            True if the file exceeds the size limit and should be excluded,
            False otherwise.

        Note:
            - Returns False for directories (directories don't have meaningful size)
            - Returns False if file size cannot be determined (permission errors, etc.)
            - For symlinks, checks the target file size by following the link
        """
        try:
            path_obj = Path(path)

            # Only check files, not directories
            if not path_obj.is_file():
                return False

            # Get file size, following symlinks to check target size
            file_size = path_obj.stat().st_size
            return file_size > self.max_size_bytes

        except (OSError, FileNotFoundError, PermissionError):
            # If we can't determine size, don't exclude
            return False

    def has_rules(self) -> bool:
        """Check if any size rules are configured.

        Returns:
            True if size limits are configured, False otherwise.
        """
        return self.max_size_bytes > 0
