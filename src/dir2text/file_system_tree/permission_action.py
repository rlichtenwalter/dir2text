"""Permission action enum for handling permission errors during directory traversal."""

from enum import Enum


class PermissionAction(str, Enum):
    """Action to take when encountering permission errors during directory traversal.

    Values:
        IGNORE: Continue traversal silently, skipping inaccessible items (default behavior)
        RAISE: Raise a PermissionError immediately when access is denied
    """

    IGNORE = "ignore"
    RAISE = "raise"
