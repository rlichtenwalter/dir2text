"""Unit tests for the permission_action module."""

from dir2text.file_system_tree.permission_action import PermissionAction


def test_permission_action_enum():
    """Test the PermissionAction enum values."""
    assert PermissionAction.IGNORE == "ignore"
    assert PermissionAction.RAISE == "raise"

    # Test string conversion works both ways
    assert PermissionAction("ignore") == PermissionAction.IGNORE
    assert PermissionAction("raise") == PermissionAction.RAISE


def test_permission_action_comparison():
    """Test comparing PermissionAction enum with strings."""
    assert PermissionAction.IGNORE == "ignore"
    assert PermissionAction.RAISE == "raise"
    assert "ignore" == PermissionAction.IGNORE
    assert "raise" == PermissionAction.RAISE
    assert PermissionAction.IGNORE != "raise"
    assert PermissionAction.RAISE != "ignore"
