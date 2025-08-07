"""Unit tests for size-based exclusion rules."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from dir2text.exclusion_rules.size_rules import SizeExclusionRules, parse_file_size


class TestParsFileSize:
    """Test the parse_file_size utility function."""

    def test_parse_bytes_only(self):
        """Test parsing raw byte values."""
        assert parse_file_size("1024") == 1024
        assert parse_file_size("0") == 0
        assert parse_file_size("999999") == 999999

    def test_parse_human_readable_decimal(self):
        """Test parsing decimal units (KB, MB, GB)."""
        # These tests assume humanfriendly standard behavior
        assert parse_file_size("1KB") == 1000
        assert parse_file_size("1MB") == 1000000
        assert parse_file_size("1GB") == 1000000000
        assert parse_file_size("2.5MB") == 2500000

    def test_parse_human_readable_binary(self):
        """Test parsing binary units (KiB, MiB, GiB)."""
        assert parse_file_size("1KiB") == 1024
        assert parse_file_size("1MiB") == 1048576
        assert parse_file_size("1GiB") == 1073741824

    def test_parse_with_spaces(self):
        """Test parsing with spaces in format."""
        assert parse_file_size("1 GB") == 1000000000
        assert parse_file_size("2.5 MB") == 2500000

    def test_parse_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid size format"):
            parse_file_size("invalid")

        with pytest.raises(ValueError, match="Invalid size format"):
            parse_file_size("")

        with pytest.raises(ValueError, match="Invalid size format"):
            parse_file_size("1XB")  # Invalid unit

    def test_humanfriendly_not_available(self):
        """Test error when humanfriendly library is not available."""
        # Simulate ImportError from humanfriendly by mocking the import
        with patch("builtins.__import__") as mock_import:
            mock_import.side_effect = ImportError("No module named 'humanfriendly'")
            with pytest.raises(ImportError, match="humanfriendly is required"):
                parse_file_size("1GB")


class TestSizeExclusionRules:
    """Test the SizeExclusionRules class."""

    def test_init_with_string(self):
        """Test initialization with human-readable size string."""
        rules = SizeExclusionRules("1MB")
        assert rules.max_size_bytes == 1000000

    def test_init_with_int(self):
        """Test initialization with integer bytes."""
        rules = SizeExclusionRules(1048576)  # 1 MiB
        assert rules.max_size_bytes == 1048576

    def test_init_with_negative_int(self):
        """Test that negative sizes are rejected."""
        with pytest.raises(ValueError, match="Size cannot be negative"):
            SizeExclusionRules(-1)

    def test_init_with_invalid_type(self):
        """Test that invalid types are rejected."""
        with pytest.raises(ValueError, match="max_size must be string or int"):
            SizeExclusionRules(1.5)  # float

        with pytest.raises(ValueError, match="max_size must be string or int"):
            SizeExclusionRules(None)

    def test_init_with_invalid_string(self):
        """Test that invalid size strings are rejected."""
        with pytest.raises(ValueError, match="Invalid size format"):
            SizeExclusionRules("invalid_size")

    def test_exclude_file_within_limit(self):
        """Test that files within size limit are not excluded."""
        rules = SizeExclusionRules(1000)  # 1000 bytes limit

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"small content")  # Less than 1000 bytes
            temp_path = f.name

        try:
            assert not rules.exclude(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_exclude_file_exceeds_limit(self):
        """Test that files exceeding size limit are excluded."""
        rules = SizeExclusionRules(10)  # 10 bytes limit

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"this content is longer than 10 bytes")
            temp_path = f.name

        try:
            assert rules.exclude(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_exclude_directory(self):
        """Test that directories are never excluded."""
        rules = SizeExclusionRules(0)  # Even 0 bytes limit

        with tempfile.TemporaryDirectory() as temp_dir:
            assert not rules.exclude(temp_dir)

    def test_exclude_nonexistent_file(self):
        """Test that nonexistent files are not excluded."""
        rules = SizeExclusionRules(1000)
        assert not rules.exclude("/nonexistent/file.txt")

    def test_exclude_permission_error(self):
        """Test that files with permission errors are not excluded."""
        rules = SizeExclusionRules(1000)

        # Mock Path.is_file to return True but stat to raise PermissionError
        with patch("pathlib.Path.is_file", return_value=True):
            with patch("pathlib.Path.stat", side_effect=PermissionError()):
                assert not rules.exclude("/some/path")

    def test_exclude_symlink_to_large_file(self):
        """Test that symlinks to large files are excluded based on target size."""
        rules = SizeExclusionRules(10)

        with tempfile.NamedTemporaryFile(delete=False) as target_file:
            target_file.write(b"this content exceeds 10 bytes")
            target_path = target_file.name

        with tempfile.TemporaryDirectory() as temp_dir:
            symlink_path = Path(temp_dir) / "symlink"
            try:
                symlink_path.symlink_to(target_path)
                # Should be excluded because target file is large
                assert rules.exclude(str(symlink_path))
            finally:
                Path(target_path).unlink()

    def test_has_rules(self):
        """Test the has_rules method."""
        rules = SizeExclusionRules(1000)
        assert rules.has_rules()

        # Edge case: zero size limit still counts as having rules
        zero_rules = SizeExclusionRules(0)
        assert not zero_rules.has_rules()

    def test_load_rules_raises_not_implemented(self):
        """Test that load_rules raises NotImplementedError."""
        rules = SizeExclusionRules("1GB")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("500MB")
            temp_path = f.name

        try:
            with pytest.raises(
                NotImplementedError, match="SizeExclusionRules doesn't support loading rules from files"
            ):
                rules.load_rules(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_rules_multiple_files_raises_not_implemented(self):
        """Test that load_rules raises NotImplementedError with multiple files."""
        rules = SizeExclusionRules("1GB")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
            f1.write("200MB")
            temp_path1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
            f2.write("300MB")
            temp_path2 = f2.name

        try:
            with pytest.raises(
                NotImplementedError, match="SizeExclusionRules doesn't support loading rules from files"
            ):
                rules.load_rules([temp_path1, temp_path2])
        finally:
            Path(temp_path1).unlink()
            Path(temp_path2).unlink()

    def test_load_rules_nonexistent_file_raises_not_implemented(self):
        """Test that load_rules raises NotImplementedError even with nonexistent file."""
        rules = SizeExclusionRules("1GB")

        with pytest.raises(NotImplementedError, match="SizeExclusionRules doesn't support loading rules from files"):
            rules.load_rules("/nonexistent/file.txt")

    def test_load_rules_invalid_content_raises_not_implemented(self):
        """Test that load_rules raises NotImplementedError even with invalid content."""
        rules = SizeExclusionRules("1GB")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("invalid_size_format")
            temp_path = f.name

        try:
            with pytest.raises(
                NotImplementedError, match="SizeExclusionRules doesn't support loading rules from files"
            ):
                rules.load_rules(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_rules_empty_file_raises_not_implemented(self):
        """Test that load_rules raises NotImplementedError even with empty file."""
        rules = SizeExclusionRules("1GB")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            with pytest.raises(
                NotImplementedError, match="SizeExclusionRules doesn't support loading rules from files"
            ):
                rules.load_rules(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_add_rule_raises_not_implemented(self):
        """Test that add_rule raises NotImplementedError."""
        rules = SizeExclusionRules("1GB")

        with pytest.raises(NotImplementedError, match="SizeExclusionRules doesn't support adding individual rules"):
            rules.add_rule("500MB")

    def test_add_rule_invalid_raises_not_implemented(self):
        """Test that add_rule raises NotImplementedError even with invalid format."""
        rules = SizeExclusionRules("1GB")

        with pytest.raises(NotImplementedError, match="SizeExclusionRules doesn't support adding individual rules"):
            rules.add_rule("invalid_format")

    def test_add_rule_with_whitespace_raises_not_implemented(self):
        """Test that add_rule raises NotImplementedError even with whitespace."""
        rules = SizeExclusionRules("1GB")

        with pytest.raises(NotImplementedError, match="SizeExclusionRules doesn't support adding individual rules"):
            rules.add_rule("  500MB  ")
