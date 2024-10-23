from abc import ABC, abstractmethod


class BaseExclusionRules(ABC):
    """
    Abstract base class defining the interface for file/directory exclusion rules.

    This class serves as a contract for implementing various types of exclusion rules
    (e.g., .gitignore-style rules) that determine which files and directories should
    be excluded from processing. Concrete implementations must provide logic for both
    loading rules from a file and checking if a given path should be excluded.

    Example:
        >>> import os
        >>> # Define a simple concrete implementation
        >>> class SimpleExclusionRules(BaseExclusionRules):
        ...     def __init__(self, rules_file: str):
        ...         self._has_tmp = False
        ...         self.load_rules(rules_file)
        ...
        ...     def exclude(self, path: str) -> bool:
        ...         return self._has_tmp and path.endswith('.tmp')
        ...
        ...     def load_rules(self, rules_file: str) -> None:
        ...         if not os.path.exists(rules_file):
        ...             raise FileNotFoundError(f"Rules file not found: {rules_file}")
        ...         # Simple rule parsing: if file contains '.tmp', exclude .tmp files
        ...         with open(rules_file, 'r') as f:
        ...             self._has_tmp = '.tmp' in f.read()
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
            >>> # Define a simple implementation
            >>> class SimpleExclusionRules(BaseExclusionRules):
            ...     def __init__(self, rules_file: str):
            ...         self._has_tmp = False
            ...         self.load_rules(rules_file)
            ...     def exclude(self, path: str) -> bool:
            ...         return self._has_tmp and path.endswith('.tmp')
            ...     def load_rules(self, rules_file: str) -> None:
            ...         if not os.path.exists(rules_file):
            ...             raise FileNotFoundError(f"Rules file not found: {rules_file}")
            ...         with open(rules_file, 'r') as f:
            ...             self._has_tmp = '.tmp' in f.read()
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
    def load_rules(self, rules_file: str) -> None:
        """
        Load and parse exclusion rules from a file.

        This method must be implemented by concrete subclasses to read and parse
        exclusion rules from a specified file. The format of the rules file will
        depend on the specific implementation (e.g., .gitignore format).

        Args:
            rules_file (str): Path to the file containing exclusion rules.

        Raises:
            FileNotFoundError: If the rules file does not exist.

        Example:
            >>> import os
            >>> # Define a simple implementation
            >>> class SimpleExclusionRules(BaseExclusionRules):
            ...     def __init__(self, rules_file: str):
            ...         self._has_tmp = False
            ...         self.load_rules(rules_file)
            ...     def exclude(self, path: str) -> bool:
            ...         return self._has_tmp and path.endswith('.tmp')
            ...     def load_rules(self, rules_file: str) -> None:
            ...         if not os.path.exists(rules_file):
            ...             raise FileNotFoundError(f"Rules file not found: {rules_file}")
            ...         with open(rules_file, 'r') as f:
            ...             self._has_tmp = '.tmp' in f.read()
            >>> import tempfile
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            ...     _ = f.write('*.tmp')
            >>> rules = SimpleExclusionRules(f.name)  # Calls load_rules internally
            >>> os.path.exists(f.name)  # Verify the file exists
            True
            >>> os.unlink(f.name)  # Clean up
        """
        pass
