"""Implementation of exclusion rules using .gitignore pattern syntax."""

from os import PathLike
from pathlib import Path
from typing import Optional, Sequence, Union

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern  # type: ignore

from dir2text.types import PathType

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

    Multiple rule files can be provided during initialization or added incrementally
    with load_rules(). Rules from all files are combined, with later rules potentially
    overriding earlier ones (particularly for negation patterns with !).

    Individual rules can also be added directly using add_rule(), which accepts the same
    pattern syntax as .gitignore files.

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
        >>> # Add individual rules directly
        >>> rules.add_rule("*.log")
        >>> rules.exclude("app.log")
        True
        >>> # Clean up the temporary file
        >>> os.unlink(f.name)

    Note:
        The paths provided to exclude() should use forward slashes (/) as path separators,
        even on Windows systems, to match Git's behavior.
    """

    def __init__(self, rules_files: Optional[Union[PathType, Sequence[PathType]]] = None):
        """Initialize GitIgnoreExclusionRules with patterns from specified files.

        Args:
            rules_files: Path(s) to the file(s) containing .gitignore patterns.
                     Can be a single path-like object or a sequence of path-like objects.

        Raises:
            FileNotFoundError: If any rules file does not exist.

        Example:
            >>> import tempfile
            >>> import os
            >>> # Create temporary gitignore files
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            ...     _ = f1.write('*.pyc\\n')
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            ...     _ = f2.write('*.log\\n')
            >>> # Initialize with both files
            >>> rules = GitIgnoreExclusionRules([f1.name, f2.name])
            >>> rules.exclude("test.pyc")
            True
            >>> rules.exclude("test.log")
            True
            >>> # Clean up
            >>> os.unlink(f1.name)
            >>> os.unlink(f2.name)
        """
        # Initialize with empty spec
        self.spec = PathSpec.from_lines(GitWildMatchPattern, [])

        # Load rules if provided
        if rules_files is not None:
            self.load_rules(rules_files)

    def exclude(self, path: str) -> bool:
        """Check if a path should be excluded based on the loaded .gitignore patterns.

        This method matches the provided path against all loaded patterns using Git's
        pattern matching rules. The path is matched exactly as provided - no path
        normalization is performed.

        Args:
            path: The path to check. Can be any path-like object.

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

    def load_rules(self, rules_files: Union[PathType, Sequence[PathType]]) -> None:
        """Load and combine .gitignore patterns from one or more files.

        This method reads patterns from the specified file(s) and adds them to the
        existing PathSpec matcher. Patterns are processed in the order they are added,
        with later patterns potentially overriding earlier ones (especially in the
        case of negation with !).

        Args:
            rules_files: Path(s) to file(s) containing .gitignore patterns.
                       Can be any path-like object or sequence of path-like objects.

        Raises:
            FileNotFoundError: If any rules file does not exist.

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
            >>> # Add second rules file
            >>> rules.load_rules(f2.name)
            >>> rules.exclude("important.txt")
            False
            >>> # Clean up
            >>> os.unlink(f1.name)
            >>> os.unlink(f2.name)
        """
        # Convert to list if it's a single path
        if isinstance(rules_files, (str, PathLike)):
            rules_files = [rules_files]

        # Process each rules file
        for rules_file in rules_files:
            path = Path(rules_file)
            if not path.exists():
                raise FileNotFoundError(f"Rules file not found: {path}")

            with open(path, "r") as f:
                gitignore_content = f.read().splitlines()

            # Add these patterns to our existing spec
            new_patterns = PathSpec.from_lines(GitWildMatchPattern, gitignore_content).patterns

            # Ensure patterns is a list that supports extend
            if not hasattr(self.spec.patterns, "extend"):
                self.spec.patterns = list(self.spec.patterns)

            self.spec.patterns.extend(new_patterns)

    def add_rule(self, rule: str) -> None:
        """Add a single .gitignore pattern directly.

        This method adds an individual .gitignore pattern to the existing rules.
        The pattern follows the same syntax as a line in a .gitignore file.
        Patterns are processed in the order they are added, with later patterns
        potentially overriding earlier ones.

        Args:
            rule: A single .gitignore pattern to add (e.g., "*.pyc", "node_modules/",
                 "!important.txt").

        Example:
            >>> rules = GitIgnoreExclusionRules()
            >>> rules.add_rule("*.pyc")
            >>> rules.exclude("test.pyc")
            True
            >>> rules.exclude("test.py")
            False
            >>> # Negation works too
            >>> rules.add_rule("!important.pyc")
            >>> rules.exclude("important.pyc")
            False
            >>> # Directory patterns
            >>> rules.add_rule("build/")
            >>> rules.exclude("build/output.txt")
            True
        """
        # Create a new pattern from the rule and add it to the existing patterns
        new_pattern = GitWildMatchPattern(rule)

        # Ensure patterns is a list that supports append
        if not hasattr(self.spec.patterns, "append"):
            self.spec.patterns = list(self.spec.patterns)

        self.spec.patterns.append(new_pattern)
