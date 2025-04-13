"""Unit tests for the FileIdentifier class."""

from dir2text.file_system_tree.file_identifier import FileIdentifier


def test_file_identifier():
    """Test the FileIdentifier class functionality."""
    # Create two identifiers with the same values
    id1 = FileIdentifier(123, 456)
    id2 = FileIdentifier(123, 456)

    # Create one with different values
    id3 = FileIdentifier(789, 456)

    # Test equality
    assert id1 == id2
    assert id1 != id3
    assert id1 != "not an identifier"

    # Test hash
    assert hash(id1) == hash(id2)
    assert hash(id1) != hash(id3)

    # Test in a set
    id_set = {id1, id3}
    assert len(id_set) == 2
    assert id2 in id_set  # id2 should be treated as equivalent to id1

    # Test repr
    assert repr(id1) == "FileIdentifier(device_id=123, inode_number=456)"
