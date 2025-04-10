"""Directory to text conversion utilities.

This package provides tools for converting directory structures into
text formats suitable for use with Large Language Models (LLMs).
"""

from importlib.metadata import PackageNotFoundError, version

# Expose the version for both programmatic use and CLI
try:
    __version__ = version("dir2text")
except PackageNotFoundError:
    __version__ = "unknown"
