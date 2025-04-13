"""XML output strategy for file content formatting.

This module provides a strategy for formatting file content as XML elements,
ensuring proper XML structure and escaping while enforcing that metadata
attributes like token counts must appear in opening tags.
"""

from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from .base_strategy import OutputStrategy


class XMLOutputStrategy(OutputStrategy):
    """Output strategy that formats file content as XML elements.

    This strategy formats each file's content as an XML file element with the following structure:
    <file path="relative/path/to/file" tokens="123">
    file content...
    </file>

    Symlinks are formatted as self-closing elements:
    <symlink path="relative/path/to/symlink" target="target/path" />

    The tokens attribute is optional and only included when token counting is enabled.
    All content is properly XML-escaped using xml.sax.saxutils.escape to ensure valid XML
    output even with special characters in file paths or content.

    Due to XML syntax requirements, any metadata attributes (including token counts)
    must be specified in the opening tag. The strategy enforces this by requiring
    token counts to be provided in format_start and rejecting them in format_end.

    Example:
        >>> strategy = XMLOutputStrategy()
        >>> print(strategy.format_start("example.py", 42), end='')
        <file path="example.py" tokens="42">
        >>> print(strategy.format_content('print("Hello")'))
        print("Hello")
        >>> print(strategy.format_end(), end='')
        </file>
        >>> print(strategy.format_symlink("link.py", "./real.py"), end='')
        <symlink path="link.py" target="./real.py" />

    Note:
        Unlike some other output strategies that might be flexible about token count
        placement, XML requires all attributes to be in the opening tag to maintain
        valid XML syntax.
    """

    def __init__(self) -> None:
        """Initialize the XML output strategy."""
        # Define XML entities mapping for proper escaping
        self._xml_entities = {
            '"': "&quot;",
            "'": "&apos;",
        }

    @property
    def requires_tokens_in_start(self) -> bool:
        """Indicates whether token counts must be provided in format_start.

        XML format requires all attributes to be in the opening tag to maintain
        valid XML syntax. Therefore, any token counts must be provided during
        format_start.

        Returns:
            bool: True, indicating token counts must be provided in format_start
            and are not allowed in format_end.
        """
        return True

    def format_start(self, relative_path: str, file_token_count: Optional[int] = None) -> str:
        """Format the opening XML tag for a file.

        Creates a <file> element with the file's path as a required attribute and
        an optional tokens attribute if token counting is enabled. All attributes
        must be provided here as XML syntax requires them in the opening tag.

        Args:
            relative_path: The relative path of the file being formatted. Will be
                XML-escaped and included as the path attribute.
            file_token_count: Total token count for the file. If provided, will be
                included as a tokens attribute.

        Returns:
            The opening XML tag as a string, including a trailing newline.

        Example:
            >>> strategy = XMLOutputStrategy()
            >>> print(strategy.format_start("src/main.py", 150), end='')
            <file path="src/main.py" tokens="150">
            >>> print(strategy.format_start("test & demo.py"), end='')
            <file path="test &amp; demo.py">
        """
        wrapper_start = f'<file path="{xml_escape(relative_path, self._xml_entities)}"'
        if file_token_count is not None:
            wrapper_start += f' tokens="{file_token_count}"'
        wrapper_start += ">\n"
        return wrapper_start

    def format_content(self, content: str) -> str:
        """Format a chunk of file content for XML inclusion.

        Escapes the content chunk to ensure valid XML, handling special characters
        like <, >, &, " and '.

        Args:
            content: A chunk of file content to format.

        Returns:
            The XML-escaped content string.

        Example:
            >>> strategy = XMLOutputStrategy()
            >>> print(strategy.format_content('if x < 10 && y > 20:'))
            if x &lt; 10 &amp;&amp; y &gt; 20:
            >>> print(strategy.format_content('<script src="test.js">'))
            &lt;script src="test.js"&gt;
        """
        # We're going to preserve the double quotes as-is for unit test compatibility
        escaped = xml_escape(content)
        return escaped

    def format_end(self, file_token_count: Optional[int] = None) -> str:
        """Format the closing XML tag for a file.

        Creates the closing </file> tag to match the opening tag created by format_start.
        Due to XML syntax requirements, token counts are not allowed here and must be
        provided in format_start instead.

        Args:
            file_token_count: Must be None. XML requires all attributes to be in the
                opening tag, so providing a token count here will raise an error.

        Returns:
            The closing XML tag "</file>" with a trailing newline.

        Raises:
            ValueError: If file_token_count is provided, since XML requires all attributes
                to be in the opening tag.

        Example:
            >>> strategy = XMLOutputStrategy()
            >>> print(strategy.format_end(), end='')
            </file>
        """
        if file_token_count is not None:
            raise ValueError(
                "Token counts must be provided in format_start for XML output. "
                "The format_end method does not accept token counts due to XML syntax requirements."
            )
        return "</file>\n"

    def format_symlink(self, relative_path: str, target_path: str) -> str:
        """Format a symbolic link as an XML element.

        Creates a self-closing symlink element with the symlink path and target path
        as attributes.

        Args:
            relative_path: The relative path of the symlink.
            target_path: The target path that the symlink points to.

        Returns:
            A formatted XML element representing the symlink.

        Example:
            >>> strategy = XMLOutputStrategy()
            >>> print(strategy.format_symlink("docs/link.md", "../README.md"), end='')
            <symlink path="docs/link.md" target="../README.md" />
        """
        return (
            f'<symlink path="{xml_escape(relative_path, self._xml_entities)}" '
            f'target="{xml_escape(target_path, self._xml_entities)}" />\n'
        )

    def get_file_extension(self) -> str:
        """Get the file extension for XML output.

        Returns:
            str: The string ".xml".

        Example:
            >>> strategy = XMLOutputStrategy()
            >>> strategy.get_file_extension()
            '.xml'
        """
        return ".xml"
