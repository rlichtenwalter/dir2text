"""Composite exclusion rules for combining multiple rule types."""

from typing import List, Sequence

from .base_rules import BaseExclusionRules


class CompositeExclusionRules(BaseExclusionRules):
    """Composite exclusion rules that combine multiple rule types.

    This class allows combining different types of exclusion rules (e.g., Git rules,
    size rules, time-based rules) into a single unified interface. A path is excluded
    if ANY of the constituent rules determines it should be excluded.

    This follows the logical OR pattern: if any rule says "exclude", the file is excluded.
    This is typically the desired behavior for exclusion rules.

    The composite pattern allows for flexible combinations:
    - Git rules + Size rules
    - Size rules + Time rules
    - All three together
    - Any custom rule combinations

    Attributes:
        rules (List[BaseExclusionRules]): List of constituent exclusion rules.

    Example:
        >>> from dir2text.exclusion_rules.size_rules import SizeExclusionRules
        >>> import tempfile
        >>> import os
        >>>
        >>> # Create temporary files for testing
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create a small file
        ...     small_file = os.path.join(tmpdir, "small.txt")
        ...     with open(small_file, "w") as f:
        ...         _ = f.write("small content")
        ...
        ...     # Create a large file (>10 bytes)
        ...     large_file = os.path.join(tmpdir, "large.dat")
        ...     with open(large_file, "w") as f:
        ...         _ = f.write("x" * 100)  # 100 bytes
        ...
        ...     # Create size rules (files > 50 bytes are excluded)
        ...     size_rules = SizeExclusionRules("50B")
        ...     composite = CompositeExclusionRules([size_rules])
        ...
        ...     # Test exclusions
        ...     composite.exclude(large_file)  # True (size rule - file > 50B)
        True
        >>> # Example with multiple rule types
        >>> from dir2text.exclusion_rules.size_rules import SizeExclusionRules
        >>> rule1 = SizeExclusionRules("1MB")  # Exclude files > 1MB
        >>> rule2 = SizeExclusionRules("10KB") # Exclude files > 10KB
        >>> composite = CompositeExclusionRules([rule1, rule2])
        >>> composite.exclude("small_file.txt")  # False (neither rule matches without real file)
        False
    """

    def __init__(self, rules: Sequence[BaseExclusionRules]):
        """Initialize composite exclusion rules.

        Args:
            rules: Sequence of exclusion rules to combine. Each rule must implement
                  the BaseExclusionRules interface.

        Raises:
            ValueError: If rules list is empty or contains invalid rule types.
            TypeError: If any rule doesn't implement BaseExclusionRules.

        Note:
            Rules are evaluated in the order provided. For performance, consider
            placing faster rules (like size checks) before slower ones (like pattern matching).
        """
        if not rules:
            raise ValueError("At least one exclusion rule must be provided")

        # Validate that all rules implement the correct interface
        for i, rule in enumerate(rules):
            if not isinstance(rule, BaseExclusionRules):
                raise TypeError(f"Rule at index {i} must implement BaseExclusionRules, " f"got {type(rule)}")

        self.rules: List[BaseExclusionRules] = list(rules)

    def exclude(self, path: str) -> bool:
        """Check if a path should be excluded by any constituent rule.

        Args:
            path: File or directory path to check.

        Returns:
            True if ANY of the constituent rules determines the path should be
            excluded, False if ALL rules allow the path.

        Note:
            Uses short-circuit evaluation: stops checking as soon as any rule
            returns True for exclusion.
        """
        return any(rule.exclude(path) for rule in self.rules)

    def has_rules(self) -> bool:
        """Check if any constituent rule has rules configured.

        Returns:
            True if ANY of the constituent rules has rules configured,
            False if ALL constituent rules are empty.

        Note:
            This method checks if the constituent rules have a has_rules() method
            and uses it if available. For rules that don't implement has_rules(),
            assumes they have rules configured.
        """
        for rule in self.rules:
            # Check if rule has the has_rules method and use it
            if hasattr(rule, "has_rules") and callable(rule.has_rules):
                if rule.has_rules():
                    return True
            else:
                # For rules without has_rules method, assume they have rules
                # This maintains backward compatibility
                return True
        return False

    def add_rule_object(self, rule: BaseExclusionRules) -> None:
        """Add another exclusion rule object to this composite.

        This method allows dynamic composition of rules after initialization.

        Args:
            rule: An exclusion rule object to add to the composite.

        Raises:
            TypeError: If rule doesn't implement BaseExclusionRules.
        """
        if not isinstance(rule, BaseExclusionRules):
            raise TypeError(f"Rule must implement BaseExclusionRules, got {type(rule)}")
        self.rules.append(rule)

    def remove_rule_object(self, rule: BaseExclusionRules) -> bool:
        """Remove an exclusion rule object from this composite.

        Args:
            rule: The exclusion rule object to remove.

        Returns:
            True if the rule was found and removed, False if it wasn't in the composite.
        """
        try:
            self.rules.remove(rule)
            return True
        except ValueError:
            return False

    def get_rule_count(self) -> int:
        """Get the number of constituent rules in this composite.

        Returns:
            Number of rules in this composite.
        """
        return len(self.rules)

    def get_rules(self) -> List[BaseExclusionRules]:
        """Get a copy of the constituent rules list.

        Returns:
            A new list containing all constituent rules.

        Note:
            Returns a copy to prevent external modification of the internal rules list.
        """
        return list(self.rules)
