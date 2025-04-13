from abc import ABC, abstractmethod
from typing import Sequence, Union

from dir2text.types import PathType


class BaseExclusionRules(ABC):
    """
    Abstract base class defining the interface for file/directory exclusion rules.

    This class serves as a contract for implementing various types of exclusion rules
    (e.g., .gitignore-style rules) that determine which files and directories should
    be excluded from processing. Concrete implementations must provide logic for both
    loading rules from files and checking if a given path should be excluded.

    Example:
        >>> import os
        >>> from os import PathLike
        >>> from dir2text.types import PathType
        >>> # Define a simple concrete implementation
        >>> class SimpleExclusionRules(BaseExclusionRules):
        ...     def __init__(self, rules_files: Union[PathType, Sequence[PathType]]):
        ...         self._has_tmp = False
        ...         self.load_rules(rules_files)
        ...
        ...     def exclude(self, path: str) -> bool:
        ...         return self._has_tmp and path.endswith('.tmp')
        ...
        ...     def load_rules(self, rules_files: Union[PathType, Sequence[PathType]]) -> None:
        ...         from pathlib import Path
        ...         if isinstance(rules_files, PathType):
        ...             rules_files = [rules_files]
        ...         for rules_file in rules_files:
        ...             path = Path(rules_file)
        ...             if not path.exists():
        ...                 raise FileNotFoundError(f"Rules file not found: {path}")
        ...             # Simple rule parsing: if file contains '.tmp', exclude .tmp files
        ...             with open(path, 'r') as f:
        ...                 self._has_tmp = self._has_tmp or '.tmp' in f.read()
        ...
        ...     def add_rule(self, rule: str) -> None:
        ...         # Direct pattern handling: if rule is '.tmp', exclude .tmp files
        ...         self._has_tmp = self._has_tmp or '.tmp' in rule
        >>> # Create an instance for example purposes
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        ...     _ = f.write('*.tmp')  # Add rule to exclude .tmp files
        >>> rules = SimpleExclusionRules(f.name)
        >>> rules.exclude("build/temp.txt")  # Not a .tmp file
        False
        >>> rules.exclude("build/temp.tmp")  # Is a .tmp file
        True
        >>> rules.exclude("src/main.py")     # Not a .tmp file
        False
        >>> os.unlink(f.name)  # Clean up
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

    @abstractmethod
    def load_rules(self, rules_files: Union[PathType, Sequence[PathType]]) -> None:
        """
        Load and parse exclusion rules from one or more files.

        This method must be implemented by concrete subclasses to read and parse
        exclusion rules from specified file(s). The format of the rules files will
        depend on the specific implementation (e.g., .gitignore format).

        Args:
            rules_files: Path to a file or sequence of paths containing exclusion rules.
                Can be any path-like object (str, Path, or anything implementing the PathLike protocol).

        Raises:
            FileNotFoundError: If any rules file does not exist.

        Example:
            >>> import os
            >>> # Define a simple implementation
            >>> class SimpleExclusionRules(BaseExclusionRules):
            ...     def __init__(self, rules_files):
            ...         self._has_tmp = False
            ...         self._has_log = False
            ...         self.load_rules(rules_files)
            ...     def exclude(self, path: str) -> bool:
            ...         if self._has_tmp and path.endswith('.tmp'):
            ...             return True
            ...         if self._has_log and path.endswith('.log'):
            ...             return True
            ...         return False
            ...     def load_rules(self, rules_files):
            ...         from pathlib import Path
            ...         if isinstance(rules_files, (str, Path)):
            ...             rules_files = [rules_files]
            ...         for rules_file in rules_files:
            ...             path = Path(rules_file)
            ...             if not path.exists():
            ...                 raise FileNotFoundError(f"Rules file not found: {path}")
            ...             with open(path, 'r') as f:
            ...                 content = f.read()
            ...                 self._has_tmp = self._has_tmp or '*.tmp' in content
            ...                 self._has_log = self._has_log or '*.log' in content
            ...     def add_rule(self, rule: str) -> None:
            ...         self._has_tmp = self._has_tmp or '*.tmp' in rule
            ...         self._has_log = self._has_log or '*.log' in rule
            >>> import tempfile
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            ...     _ = f.write('*.tmp')
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            ...     _ = f2.write('*.log')
            >>> rules = SimpleExclusionRules([f.name, f2.name])  # Load multiple files
            >>> rules.exclude("test.tmp")
            True
            >>> rules.exclude("test.log")
            True
            >>> rules.exclude("test.txt")
            False
            >>> os.unlink(f.name)  # Clean up
            >>> os.unlink(f2.name)  # Clean up
        """
        pass

    @abstractmethod
    def add_rule(self, rule: str) -> None:
        """
        Add a single exclusion rule directly.

        This method must be implemented by concrete subclasses to add an individual
        exclusion rule (pattern) without reading from a file. This allows for
        programmatically adding rules or accepting rules from command-line arguments.

        Args:
            rule (str): The exclusion rule to add. The format depends on the specific
                implementation (e.g., a gitignore pattern like "*.pyc").

        Example:
            >>> import os
            >>> # Define a simple implementation
            >>> class SimpleExclusionRules(BaseExclusionRules):
            ...     def __init__(self, rules_files=None):
            ...         self._has_tmp = False
            ...         self._has_log = False
            ...         if rules_files:
            ...             self.load_rules(rules_files)
            ...     def exclude(self, path: str) -> bool:
            ...         if self._has_tmp and path.endswith('.tmp'):
            ...             return True
            ...         if self._has_log and path.endswith('.log'):
            ...             return True
            ...         return False
            ...     def load_rules(self, rules_files):
            ...         from pathlib import Path
            ...         if isinstance(rules_files, (str, Path)):
            ...             rules_files = [rules_files]
            ...         for rules_file in rules_files:
            ...             path = Path(rules_file)
            ...             if not path.exists():
            ...                 raise FileNotFoundError(f"Rules file not found: {path}")
            ...             with open(path, 'r') as f:
            ...                 content = f.read()
            ...                 self._has_tmp = self._has_tmp or '*.tmp' in content
            ...                 self._has_log = self._has_log or '*.log' in content
            ...     def add_rule(self, rule: str) -> None:
            ...         self._has_tmp = self._has_tmp or '*.tmp' in rule
            ...         self._has_log = self._has_log or '*.log' in rule
            >>> # Create rules with direct pattern
            >>> rules = SimpleExclusionRules()
            >>> rules.add_rule('*.tmp')
            >>> rules.exclude('test.tmp')
            True
            >>> rules.exclude('test.txt')
            False
            >>> # Add another rule
            >>> rules.add_rule('*.log')
            >>> rules.exclude('app.log')
            True
        """
        pass
