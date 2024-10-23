"""Implementation of exclusion rules using .gitignore pattern syntax."""

import os

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern  # type: ignore

from .base_rules import BaseExclusionRules


class GitIgnoreExclusionRules(BaseExclusionRules):
    """Implementation of exclusion rules using .gitignore pattern syntax.

    This class implements the BaseExclusionRules interface using standard .gitignore pattern
    matching rules. It uses the pathspec library to match file paths against patterns in
    the same way that Git does.

    The rules support all standard .gitignore syntax including:
    - Basic globs (*, ?, [abc], [0-9], etc.)
    - Directory-specific patterns (ending in /)
    - Negation patterns (starting with !)
    - Double-asterisk matching (**)
    - Comment lines (starting with #)

    Attributes:
        spec (PathSpec): Compiled pattern matcher from the pathspec library.

    Example:
        >>> import tempfile
        >>> import os
        >>> # Create a temporary gitignore file
        >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        ...     _ = f.write('node_modules/\\n')
        >>> # Create rules with our temporary gitignore
        >>> rules = GitIgnoreExclusionRules(f.name)
        >>> rules.exclude("node_modules/package.json")
        True
        >>> # Clean up the temporary file
        >>> os.unlink(f.name)

    Note:
        The paths provided to exclude() should use forward slashes (/) as path separators,
        even on Windows systems, to match Git's behavior.
    """

    def __init__(self, rules_file: str):
        """Initialize GitIgnoreExclusionRules with patterns from a specified file.

        Args:
            rules_file (str): Path to the file containing .gitignore patterns.

        Raises:
            FileNotFoundError: If the rules file does not exist.

        Example:
            >>> import tempfile
            >>> import os
            >>> # Create a temporary gitignore file
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            ...     _ = f.write('*.pyc\\n')
            >>> # Initialize with our temporary gitignore
            >>> rules = GitIgnoreExclusionRules(f.name)
            >>> # Clean up
            >>> os.unlink(f.name)
        """
        self.spec: PathSpec
        self.load_rules(rules_file)

    def exclude(self, path: str) -> bool:
        """Check if a path should be excluded based on the loaded .gitignore patterns.

        This method matches the provided path against all loaded patterns using Git's
        pattern matching rules. The path is matched exactly as provided - no path
        normalization is performed.

        Args:
            path: The path to check. Should use forward slashes (/) as path
                separators, even on Windows.

        Returns:
            bool: True if the path matches any non-negated pattern or matches a negated
                pattern that isn't overridden by a later non-negated pattern, False
                otherwise.

        Example:
            >>> import tempfile
            >>> import os
            >>> # Create a temporary gitignore file
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            ...     _ = f.write('*.pyc\\n!important.pyc\\n')
            >>> rules = GitIgnoreExclusionRules(f.name)
            >>> rules.exclude("test.pyc")
            True
            >>> rules.exclude("important.pyc")
            False
            >>> os.unlink(f.name)
        """
        return self.spec.match_file(path)

    def load_rules(self, rules_file: str) -> None:
        """Load and compile .gitignore patterns from a file.

        This method reads patterns from the specified file and compiles them into a
        PathSpec matcher. Empty lines and lines starting with # are ignored. The patterns
        are processed in order, with later patterns potentially overriding earlier ones
        (especially in the case of negation with !).

        Args:
            rules_file (str): Path to the file containing .gitignore patterns.

        Raises:
            FileNotFoundError: If the rules file does not exist.

        Example:
            >>> import tempfile
            >>> import os
            >>> # Create temporary gitignore files
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            ...     _ = f1.write('*.txt\\n')
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            ...     _ = f2.write('!important.txt\\n')
            >>> # Load first rules file
            >>> rules = GitIgnoreExclusionRules(f1.name)
            >>> rules.exclude("test.txt")
            True
            >>> # Load second rules file
            >>> rules.load_rules(f2.name)
            >>> rules.exclude("important.txt")
            False
            >>> # Clean up
            >>> os.unlink(f1.name)
            >>> os.unlink(f2.name)
        """
        if not os.path.exists(rules_file):
            raise FileNotFoundError(f"Rules file not found: {rules_file}")
        with open(rules_file, "r") as f:
            gitignore_content = f.read().splitlines()
        self.spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_content)
