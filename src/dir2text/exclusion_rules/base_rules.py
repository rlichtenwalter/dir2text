from abc import ABC, abstractmethod
from typing import Sequence, Union

from dir2text.types import PathType


class BaseExclusionRules(ABC):
    """
    Abstract base class defining the interface for file/directory exclusion rules.

    This class serves as a contract for implementing various types of exclusion rules
    (e.g., .gitignore-style rules, size-based rules) that determine which files and
    directories should be excluded from processing. All implementations must provide
    logic for checking if a given path should be excluded. File loading and individual
    rule addition are optional capabilities that depend on the rule type.

    Example:
        >>> # Example of a file-supporting rule implementation
        >>> from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
        >>> git_rules = GitIgnoreExclusionRules()
        >>> git_rules.add_rule('*.pyc')  # Add rule programmatically
        >>> git_rules.exclude('test.pyc')
        True
        >>> git_rules.exclude('test.py')
        False
        >>>
        >>> # Example of a non-file-supporting rule implementation
        >>> from dir2text.exclusion_rules.size_rules import SizeExclusionRules
        >>> size_rules = SizeExclusionRules('1MB')  # Constructor-only configuration
        >>> size_rules.max_size_bytes
        1000000
        >>> # size_rules.load_rules('file.txt')  # Would raise NotImplementedError
    """

    @abstractmethod
    def exclude(self, path: str) -> bool:
        """
        Determine if a given path should be excluded based on the loaded rules.

        This method must be implemented by concrete subclasses to check whether a
        specific file or directory path matches any exclusion rules.

        Args:
            path (str): The file or directory path to check. This is typically a
                relative path from the root of the directory being processed.

        Returns:
            bool: True if the path should be excluded, False if it should be included.

        Example:
            >>> import os
            >>> from os import PathLike
            >>> from dir2text.types import PathType
            >>> # Define a simple implementation
            >>> class SimpleExclusionRules(BaseExclusionRules):
            ...     def __init__(self, rules_files: Union[PathType, Sequence[PathType]]):
            ...         self._has_tmp = False
            ...         self.load_rules(rules_files)
            ...     def exclude(self, path: str) -> bool:
            ...         return self._has_tmp and path.endswith('.tmp')
            ...     def load_rules(self, rules_files: Union[PathType, Sequence[PathType]]) -> None:
            ...         from pathlib import Path
            ...         if isinstance(rules_files, PathType):
            ...             rules_files = [rules_files]
            ...         for rules_file in rules_files:
            ...             path = Path(rules_file)
            ...             if not path.exists():
            ...                 raise FileNotFoundError(f"Rules file not found: {path}")
            ...             with open(path, 'r') as f:
            ...                 self._has_tmp = self._has_tmp or '.tmp' in f.read()
            ...     def add_rule(self, rule: str) -> None:
            ...         self._has_tmp = self._has_tmp or '.tmp' in rule
            >>> import tempfile
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            ...     _ = f.write('*.tmp')  # Add rule to exclude .tmp files
            >>> rules = SimpleExclusionRules(f.name)
            >>> rules.exclude("build/temp.tmp")  # Should match
            True
            >>> rules.exclude("main.py")         # Should not match
            False
            >>> os.unlink(f.name)  # Clean up
        """
        pass

    def load_rules(self, rules_files: Union[PathType, Sequence[PathType]]) -> None:
        """
        Load and parse exclusion rules from one or more files.

        This method may be overridden by subclasses that support file-based rule loading
        (e.g., .gitignore-style rules). Rule types that don't support file operations
        (e.g., size-based or composite rules) use the default implementation which raises
        NotImplementedError.

        Args:
            rules_files: Path to a file or sequence of paths containing exclusion rules.
                Can be any path-like object (str, Path, or anything implementing the PathLike protocol).

        Raises:
            NotImplementedError: If this rule type doesn't support loading from files.
            FileNotFoundError: If any rules file does not exist (for file-supporting rule types).
        """
        raise NotImplementedError(f"{self.__class__.__name__} doesn't support loading rules from files.")

    def add_rule(self, rule: str) -> None:
        """
        Add a single exclusion rule directly.

        This method may be overridden by subclasses that support programmatic rule addition
        (e.g., pattern-based rules). Rule types that don't support individual rule addition
        (e.g., size-based or composite rules) use the default implementation which raises
        NotImplementedError.

        Args:
            rule (str): The exclusion rule to add. The format depends on the specific
                implementation (e.g., a gitignore pattern like "*.pyc").

        Raises:
            NotImplementedError: If this rule type doesn't support adding individual rules.
        """
        raise NotImplementedError(f"{self.__class__.__name__} doesn't support adding individual rules.")
