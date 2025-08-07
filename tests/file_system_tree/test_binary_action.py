"""Tests for the BinaryAction enum."""

from dir2text.file_system_tree.binary_action import BinaryAction


def test_binary_action_enum():
    """Test the BinaryAction enum values."""
    assert BinaryAction.IGNORE == "ignore"
    assert BinaryAction.RAISE == "raise"
    assert BinaryAction.ENCODE == "encode"

    # Test string conversion works both ways
    assert BinaryAction("ignore") == BinaryAction.IGNORE
    assert BinaryAction("raise") == BinaryAction.RAISE
    assert BinaryAction("encode") == BinaryAction.ENCODE


def test_binary_action_comparison():
    """Test comparing BinaryAction enum with strings."""
    assert BinaryAction.IGNORE == "ignore"
    assert BinaryAction.RAISE == "raise"
    assert BinaryAction.ENCODE == "encode"
    assert "ignore" == BinaryAction.IGNORE
    assert "raise" == BinaryAction.RAISE
    assert "encode" == BinaryAction.ENCODE
    assert BinaryAction.IGNORE != "raise"
    assert BinaryAction.RAISE != "ignore"
    assert BinaryAction.ENCODE != "ignore"
