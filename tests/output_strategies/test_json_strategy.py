import json

import pytest

from dir2text.output_strategies.json_strategy import JSONOutputStrategy


@pytest.fixture
def json_strategy():
    """Fixture to provide a clean JSONOutputStrategy instance for each test."""
    return JSONOutputStrategy()


def test_format_start():
    """Test the format_start method with various inputs."""
    strategy = JSONOutputStrategy()

    # Test basic path with default text type
    basic = strategy.format_start("test.py")
    assert basic == '{"type": "file", "path": "test.py", "content_type": "text", "content": "'

    # Test path with special characters
    special = strategy.format_start('test"file.py')
    assert special == '{"type": "file", "path": "test\\"file.py", "content_type": "text", "content": "'

    # Test with binary type
    binary = strategy.format_start("image.png", "binary")
    assert binary == '{"type": "file", "path": "image.png", "content_type": "binary", "content": "'

    # Test with token count
    with_tokens = strategy.format_start("test.py", "text", 42)
    assert with_tokens == '{"type": "file", "path": "test.py", "content_type": "text", "content": "'


def test_format_content():
    """Test the format_content method with various inputs."""
    strategy = JSONOutputStrategy()

    # Test plain text
    assert strategy.format_content("Hello, world!") == "Hello, world!"

    # Test content with special JSON characters
    assert strategy.format_content('test"quote"') == 'test\\"quote\\"'

    # Test content with newlines and special characters
    assert strategy.format_content('line1\nline2\t"test"') == 'line1\\nline2\\t\\"test\\"'


def test_format_end():
    """Test the format_end method."""
    strategy = JSONOutputStrategy()

    # Test basic end (no tokens)
    assert strategy.format_end(None) == '"}'

    # Test end with token count
    assert strategy.format_end(42) == '", "tokens": 42}'


def test_format_symlink():
    """Test the format_symlink method."""
    strategy = JSONOutputStrategy()

    # Test basic symlink
    symlink_output = strategy.format_symlink("link.py", "./real.py")
    parsed = json.loads(symlink_output)
    assert parsed["type"] == "symlink"
    assert parsed["path"] == "link.py"
    assert parsed["target"] == "./real.py"

    # Test symlink with special characters
    special_output = strategy.format_symlink('link"with"quotes.txt', "../path/with\\backslash")
    special_parsed = json.loads(special_output)
    assert special_parsed["path"] == 'link"with"quotes.txt'
    assert special_parsed["target"] == "../path/with\\backslash"

    # Verify proper escaping in the raw output
    assert '\\"' in special_output  # Should contain escaped quotes
    assert "\\\\" in special_output  # Should contain escaped backslash


def test_file_extension():
    """Test the get_file_extension method."""
    strategy = JSONOutputStrategy()
    assert strategy.get_file_extension() == ".json"


def test_complete_file_output():
    """Test a complete file output sequence."""
    strategy = JSONOutputStrategy()

    output = []
    output.append(strategy.format_start("test.py"))
    output.append(strategy.format_content('def test():\n    print("Hello")'))
    output.append(strategy.format_end())

    complete_output = "".join(output)

    # Verify the output is valid JSON
    parsed = json.loads(complete_output)
    assert parsed["type"] == "file"
    assert parsed["path"] == "test.py"
    assert parsed["content"] == 'def test():\n    print("Hello")'


def test_complete_file_output_start_tokens():
    """Test a complete file output sequence."""
    strategy = JSONOutputStrategy()

    output = []
    output.append(strategy.format_start("test.py", "text", 100))
    output.append(strategy.format_content('def test():\n    print("Hello")'))
    output.append(strategy.format_end())

    complete_output = "".join(output)

    # Verify the output is valid JSON
    parsed = json.loads(complete_output)
    assert parsed["type"] == "file"
    assert parsed["path"] == "test.py"
    assert parsed["content_type"] == "text"
    assert parsed["content"] == 'def test():\n    print("Hello")'
    assert parsed["tokens"] == 100


def test_complete_file_output_end_tokens():
    """Test a complete file output sequence."""
    strategy = JSONOutputStrategy()

    output = []
    output.append(strategy.format_start("test.py"))
    output.append(strategy.format_content('def test():\n    print("Hello")'))
    output.append(strategy.format_end(100))

    complete_output = "".join(output)

    # Verify the output is valid JSON
    parsed = json.loads(complete_output)
    assert parsed["type"] == "file"
    assert parsed["path"] == "test.py"
    assert parsed["content"] == 'def test():\n    print("Hello")'
    assert parsed["tokens"] == 100


def test_complete_file_output_both_equal_tokens():
    """Test a complete file output sequence."""
    strategy = JSONOutputStrategy()

    output = []
    output.append(strategy.format_start("test.py", 100))
    output.append(strategy.format_content('def test():\n    print("Hello")'))
    output.append(strategy.format_end(100))

    complete_output = "".join(output)

    # Verify the output is valid JSON
    parsed = json.loads(complete_output)
    assert parsed["type"] == "file"
    assert parsed["path"] == "test.py"
    assert parsed["content"] == 'def test():\n    print("Hello")'
    assert parsed["tokens"] == 100


def test_complete_file_output_both_unequal_tokens():
    """Test a complete file output sequence."""
    strategy = JSONOutputStrategy()

    output = []
    output.append(strategy.format_start("test.py", "text", 99))
    output.append(strategy.format_content('def test():\n    print("Hello")'))
    with pytest.raises(ValueError):
        # End token count doesn't match start token count
        output.append(strategy.format_end(100))


def test_json_escaping():
    """Test proper escaping of special characters in JSON output."""
    strategy = JSONOutputStrategy()

    output = []
    output.append(strategy.format_start('test"file".py', None))
    output.append(strategy.format_content('line1\n"quoted"\t\\path'))
    output.append(strategy.format_end(None))

    complete_output = "".join(output)

    # Verify the output is valid JSON and preserves special characters
    parsed = json.loads(complete_output)
    assert parsed["type"] == "file"
    assert parsed["path"] == 'test"file".py'
    assert parsed["content"] == 'line1\n"quoted"\t\\path'


def test_json_formatting_consistency():
    """Test that the JSON formatting remains consistent and valid across multiple calls."""
    strategy = JSONOutputStrategy()

    def create_and_verify_json(path, content, tokens=None):
        """Helper to create and verify a complete JSON output."""
        parts = [strategy.format_start(path, tokens), strategy.format_content(content), strategy.format_end(tokens)]
        complete = "".join(parts)
        # Verify it's valid JSON
        parsed = json.loads(complete)
        return parsed

    # Test multiple combinations
    test_cases = [
        ("simple.txt", "Hello"),
        ("path with spaces.txt", "Content with spaces"),
        ('special"chars.txt', 'Content with "quotes"'),
        ("with_tokens.txt", "Content", 42),
    ]

    for args in test_cases:
        parsed = create_and_verify_json(*args)
        assert parsed["type"] == "file"
        assert parsed["path"] == args[0]
        assert parsed["content"] == args[1]
        if len(args) > 2:
            assert parsed["tokens"] == args[2]


def test_json_symlink_valid_format():
    """Test that the symlink format generates valid JSON."""
    strategy = JSONOutputStrategy()

    # Test symlink format
    symlink_json = strategy.format_symlink("link.py", "./target.py")

    # Verify it's valid JSON
    parsed = json.loads(symlink_json)
    assert parsed["type"] == "symlink"
    assert parsed["path"] == "link.py"
    assert parsed["target"] == "./target.py"
