import pytest

from dir2text.output_strategies.xml_strategy import XMLOutputStrategy


@pytest.fixture
def xml_strategy():
    """Fixture to provide a clean XMLOutputStrategy instance for each test."""
    return XMLOutputStrategy()


def test_format_start():
    """Test the format_start method with various inputs."""
    strategy = XMLOutputStrategy()

    # Test basic path
    assert strategy.format_start("test.py", None) == '<file path="test.py">\n'

    # Test path with special characters
    assert strategy.format_start("test & file.py", None) == '<file path="test &amp; file.py">\n'

    # Test with token count
    assert strategy.format_start("test.py", 42) == '<file path="test.py" tokens="42">\n'


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
    output.append(strategy.format_start("test.py", 100))
    output.append(strategy.format_content('def test():\n    print("Hello")'))
    output.append(strategy.format_end())

    expected = '<file path="test.py" tokens="100">\ndef test():\n    print("Hello")</file>\n'

    assert "".join(output) == expected
