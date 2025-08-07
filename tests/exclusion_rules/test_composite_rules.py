"""Unit tests for composite exclusion rules."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from dir2text.exclusion_rules.base_rules import BaseExclusionRules
from dir2text.exclusion_rules.composite_rules import CompositeExclusionRules
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.exclusion_rules.size_rules import SizeExclusionRules


class MockExclusionRules(BaseExclusionRules):
    """Mock exclusion rules for testing."""

    def __init__(self, exclude_patterns=None, has_rules_result=True):
        self.exclude_patterns = exclude_patterns or []
        self.has_rules_result = has_rules_result
        self.loaded_files = []
        self.added_rules = []

    def exclude(self, path: str) -> bool:
        return path in self.exclude_patterns

    def load_rules(self, rules_files):
        # Store loaded files for testing
        if isinstance(rules_files, (str, Path)):
            self.loaded_files.append(str(rules_files))
        else:
            self.loaded_files.extend(str(f) for f in rules_files)

    def add_rule(self, rule: str) -> None:
        self.added_rules.append(rule)

    def has_rules(self) -> bool:
        return self.has_rules_result


class TestCompositeExclusionRules:
    """Test the CompositeExclusionRules class."""

    def test_init_with_single_rule(self):
        """Test initialization with a single rule."""
        mock_rule = MockExclusionRules()
        composite = CompositeExclusionRules([mock_rule])

        assert len(composite.get_rules()) == 1
        assert composite.get_rules()[0] is mock_rule

    def test_init_with_multiple_rules(self):
        """Test initialization with multiple rules."""
        mock_rule1 = MockExclusionRules()
        mock_rule2 = MockExclusionRules()
        composite = CompositeExclusionRules([mock_rule1, mock_rule2])

        assert composite.get_rule_count() == 2
        assert mock_rule1 in composite.get_rules()
        assert mock_rule2 in composite.get_rules()

    def test_init_with_empty_rules(self):
        """Test that empty rules list raises ValueError."""
        with pytest.raises(ValueError, match="At least one exclusion rule must be provided"):
            CompositeExclusionRules([])

    def test_init_with_invalid_rule_type(self):
        """Test that invalid rule types raise TypeError."""
        with pytest.raises(TypeError, match="Rule at index 0 must implement BaseExclusionRules"):
            CompositeExclusionRules(["not a rule"])

        # Test mixed valid and invalid
        mock_rule = MockExclusionRules()
        with pytest.raises(TypeError, match="Rule at index 1 must implement BaseExclusionRules"):
            CompositeExclusionRules([mock_rule, "invalid"])

    def test_exclude_none_match(self):
        """Test exclusion when no rules match."""
        rule1 = MockExclusionRules(exclude_patterns=["file1.txt"])
        rule2 = MockExclusionRules(exclude_patterns=["file2.txt"])
        composite = CompositeExclusionRules([rule1, rule2])

        assert not composite.exclude("file3.txt")

    def test_exclude_single_match(self):
        """Test exclusion when one rule matches."""
        rule1 = MockExclusionRules(exclude_patterns=["file1.txt"])
        rule2 = MockExclusionRules(exclude_patterns=["file2.txt"])
        composite = CompositeExclusionRules([rule1, rule2])

        assert composite.exclude("file1.txt")
        assert composite.exclude("file2.txt")

    def test_exclude_multiple_match(self):
        """Test exclusion when multiple rules match."""
        rule1 = MockExclusionRules(exclude_patterns=["common.txt"])
        rule2 = MockExclusionRules(exclude_patterns=["common.txt"])
        composite = CompositeExclusionRules([rule1, rule2])

        # Should return True if any rule matches
        assert composite.exclude("common.txt")

    def test_exclude_short_circuit(self):
        """Test that exclusion uses short-circuit evaluation."""
        rule1 = MockExclusionRules(exclude_patterns=["file.txt"])
        rule2 = Mock(spec=BaseExclusionRules)
        rule2.exclude = Mock(return_value=False)

        composite = CompositeExclusionRules([rule1, rule2])

        # Should return True and not call rule2.exclude
        assert composite.exclude("file.txt")
        rule2.exclude.assert_not_called()

    def test_load_rules_raises_not_implemented(self):
        """Test that load_rules raises NotImplementedError."""
        rule1 = MockExclusionRules()
        rule2 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1, rule2])

        with pytest.raises(
            NotImplementedError, match="CompositeExclusionRules doesn't support loading rules from files"
        ):
            composite.load_rules("/path/to/rules.txt")

    def test_load_rules_multiple_files_raises_not_implemented(self):
        """Test loading rules from multiple files raises NotImplementedError."""
        rule1 = MockExclusionRules()
        rule2 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1, rule2])

        files = ["/path/to/rules1.txt", "/path/to/rules2.txt"]
        with pytest.raises(
            NotImplementedError, match="CompositeExclusionRules doesn't support loading rules from files"
        ):
            composite.load_rules(files)

    def test_add_rule_raises_not_implemented(self):
        """Test that add_rule raises NotImplementedError."""
        rule1 = MockExclusionRules()
        rule2 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1, rule2])

        with pytest.raises(
            NotImplementedError, match="CompositeExclusionRules doesn't support adding individual rules"
        ):
            composite.add_rule("*.tmp")

    def test_has_rules_any_true(self):
        """Test has_rules returns True if any rule has rules."""
        rule1 = MockExclusionRules(has_rules_result=False)
        rule2 = MockExclusionRules(has_rules_result=True)
        rule3 = MockExclusionRules(has_rules_result=False)
        composite = CompositeExclusionRules([rule1, rule2, rule3])

        assert composite.has_rules()

    def test_has_rules_all_false(self):
        """Test has_rules returns False if all rules have no rules."""
        rule1 = MockExclusionRules(has_rules_result=False)
        rule2 = MockExclusionRules(has_rules_result=False)
        composite = CompositeExclusionRules([rule1, rule2])

        assert not composite.has_rules()

    def test_has_rules_no_method(self):
        """Test has_rules with rules that don't implement has_rules method."""
        # Create a rule without has_rules method
        rule_without_method = Mock(spec=BaseExclusionRules)
        del rule_without_method.has_rules  # Remove the method

        rule_with_method = MockExclusionRules(has_rules_result=False)
        composite = CompositeExclusionRules([rule_without_method, rule_with_method])

        # Should return True because rule_without_method is assumed to have rules
        assert composite.has_rules()

    def test_add_rule_object(self):
        """Test adding rule objects dynamically."""
        rule1 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1])

        rule2 = MockExclusionRules()
        composite.add_rule_object(rule2)

        assert composite.get_rule_count() == 2
        assert rule2 in composite.get_rules()

    def test_add_rule_object_invalid_type(self):
        """Test adding invalid rule object type."""
        rule1 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1])

        with pytest.raises(TypeError, match="Rule must implement BaseExclusionRules"):
            composite.add_rule_object("not a rule")

    def test_remove_rule_object_success(self):
        """Test removing rule objects successfully."""
        rule1 = MockExclusionRules()
        rule2 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1, rule2])

        result = composite.remove_rule_object(rule1)

        assert result is True
        assert composite.get_rule_count() == 1
        assert rule1 not in composite.get_rules()
        assert rule2 in composite.get_rules()

    def test_remove_rule_object_not_found(self):
        """Test removing rule object that's not in composite."""
        rule1 = MockExclusionRules()
        rule2 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1])

        result = composite.remove_rule_object(rule2)

        assert result is False
        assert composite.get_rule_count() == 1
        assert rule1 in composite.get_rules()

    def test_get_rules_returns_copy(self):
        """Test that get_rules returns a copy to prevent external modification."""
        rule1 = MockExclusionRules()
        rule2 = MockExclusionRules()
        composite = CompositeExclusionRules([rule1, rule2])

        rules_copy = composite.get_rules()
        original_count = composite.get_rule_count()

        # Modify the copy
        rules_copy.append(MockExclusionRules())

        # Original should be unchanged
        assert composite.get_rule_count() == original_count
        assert len(composite.get_rules()) == original_count


class TestCompositeExclusionRulesIntegration:
    """Integration tests with real exclusion rule classes."""

    def test_git_and_size_rules_integration(self):
        """Test combining Git and size rules in practice."""
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".gitignore") as gitignore:
            gitignore.write("*.log\n")
            gitignore_path = gitignore.name

        with tempfile.NamedTemporaryFile(delete=False) as large_file:
            large_file.write(b"x" * 2000)  # 2000 bytes
            large_file_path = large_file.name

        with tempfile.NamedTemporaryFile(delete=False) as small_file:
            small_file.write(b"small")  # 5 bytes
            small_file_path = small_file.name

        try:
            # Create rules
            git_rules = GitIgnoreExclusionRules(gitignore_path)
            size_rules = SizeExclusionRules(1000)  # 1000 byte limit
            composite = CompositeExclusionRules([git_rules, size_rules])

            # Test exclusions
            assert composite.exclude("test.log")  # Excluded by git rules
            assert composite.exclude(large_file_path)  # Excluded by size rules
            assert not composite.exclude(small_file_path)  # Not excluded by either
            assert not composite.exclude("test.txt")  # Not excluded by either

        finally:
            # Clean up
            Path(gitignore_path).unlink()
            Path(large_file_path).unlink()
            Path(small_file_path).unlink()

    def test_composite_load_rules_integration_raises_not_implemented(self):
        """Test that load_rules raises NotImplementedError even with real rule classes."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".gitignore") as gitignore:
            gitignore.write("*.tmp\n")
            gitignore_path = gitignore.name

        try:
            # Create composite with empty rules
            git_rules = GitIgnoreExclusionRules()
            size_rules = SizeExclusionRules("1GB")
            composite = CompositeExclusionRules([git_rules, size_rules])

            # Should raise NotImplementedError
            with pytest.raises(
                NotImplementedError, match="CompositeExclusionRules doesn't support loading rules from files"
            ):
                composite.load_rules(gitignore_path)

        finally:
            Path(gitignore_path).unlink()

    def test_composite_add_rule_integration_raises_not_implemented(self):
        """Test that add_rule raises NotImplementedError even with real rule classes."""
        git_rules = GitIgnoreExclusionRules()
        size_rules = SizeExclusionRules("1GB")
        composite = CompositeExclusionRules([git_rules, size_rules])

        # Should raise NotImplementedError
        with pytest.raises(
            NotImplementedError, match="CompositeExclusionRules doesn't support adding individual rules"
        ):
            composite.add_rule("*.cache")

    def test_empty_git_rules_with_size_rules(self):
        """Test composite behavior with empty git rules and active size rules."""
        # Git rules with no patterns loaded
        git_rules = GitIgnoreExclusionRules()
        size_rules = SizeExclusionRules("1KB")
        composite = CompositeExclusionRules([git_rules, size_rules])

        # Create a small and large file
        with tempfile.NamedTemporaryFile(delete=False) as small_file:
            small_file.write(b"small")
            small_file_path = small_file.name

        with tempfile.NamedTemporaryFile(delete=False) as large_file:
            large_file.write(b"x" * 2000)  # 2KB
            large_file_path = large_file.name

        try:
            # Only size rules should be active
            assert not composite.exclude(small_file_path)  # Small file allowed
            assert composite.exclude(large_file_path)  # Large file excluded

        finally:
            Path(small_file_path).unlink()
            Path(large_file_path).unlink()
