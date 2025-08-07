"""Binary action enum for handling binary files during directory traversal."""

from enum import Enum


class BinaryAction(str, Enum):
    """Action to take when encountering binary files during directory traversal.

    Values:
        IGNORE: Skip binary files silently without including them in output
        RAISE: Raise an error when a binary file is encountered (handled at higher level for warn vs fail)
        ENCODE: Include binary files in output as base64-encoded content
    """

    IGNORE = "ignore"
    RAISE = "raise"
    ENCODE = "encode"
