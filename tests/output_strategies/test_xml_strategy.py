import pytest

from dir2text.output_strategies.xml_strategy import XMLOutputStrategy


@pytest.fixture
def xml_strategy():
    """Fixture to provide a clean XMLOutputStrategy instance for each test."""
    return XMLOutputStrategy()


def test_format_start():
    """Test the format_start method with various inputs."""
    strategy = XMLOutputStrategy()

    # Test basic path with default text type
    assert strategy.format_start("test.py") == '<file path="test.py" content_type="text">\n'

    # Test path with special characters
    assert strategy.format_start("test & file.py") == '<file path="test &amp; file.py" content_type="text">\n'

    # Test with binary type
    assert strategy.format_start("image.png", "binary") == '<file path="image.png" content_type="binary">\n'

    # Test with token count
    assert strategy.format_start("test.py", "text", 42) == '<file path="test.py" content_type="text" tokens="42">\n'

    # Test binary file with token count
    assert (
        strategy.format_start("data.bin", "binary", 123)
        == '<file path="data.bin" content_type="binary" tokens="123">\n'
    )


def test_format_content():
    """Test the format_content method with various inputs."""
    strategy = XMLOutputStrategy()

    # Test plain text
    assert strategy.format_content("Hello, world!") == "Hello, world!"

    # Test content with special XML characters
    assert strategy.format_content("<test>&</test>") == "&lt;test&gt;&amp;&lt;/test&gt;"

    # Test content with multiple lines
    assert strategy.format_content("line1\nline2") == "line1\nline2"


def test_format_end():
    """Test the format_end method."""
    strategy = XMLOutputStrategy()

    # Test basic end tag
    assert strategy.format_end() == "</file>\n"

    # Test end tag with token count (should raise ValueError)
    with pytest.raises(ValueError):
        strategy.format_end(42)


def test_format_symlink():
    """Test the format_symlink method."""
    strategy = XMLOutputStrategy()

    # Test basic symlink
    assert strategy.format_symlink("link.py", "./real.py") == '<symlink path="link.py" target="./real.py" />\n'

    # Test symlink with special characters
    assert (
        strategy.format_symlink("link & symlink.txt", '../path/with "quotes"')
        == '<symlink path="link &amp; symlink.txt" target="../path/with &quot;quotes&quot;" />\n'
    )

    # Test symlink with path structure
    assert (
        strategy.format_symlink("dir1/dir2/link.md", "../../README.md")
        == '<symlink path="dir1/dir2/link.md" target="../../README.md" />\n'
    )


def test_file_extension():
    """Test the get_file_extension method."""
    strategy = XMLOutputStrategy()
    assert strategy.get_file_extension() == ".xml"


def test_complete_file_output():
    """Test a complete file output sequence."""
    strategy = XMLOutputStrategy()

    output = []
    output.append(strategy.format_start("test.py", "text", 100))
    output.append(strategy.format_content('def test():\n    print("Hello")'))
    output.append(strategy.format_end())

    expected = '<file path="test.py" content_type="text" tokens="100">\ndef test():\n    print("Hello")</file>\n'

    assert "".join(output) == expected
