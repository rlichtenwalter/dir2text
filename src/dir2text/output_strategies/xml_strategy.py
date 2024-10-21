from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from .base_strategy import OutputStrategy


class XMLOutputStrategy(OutputStrategy):
    def format_start(self, relative_path: str, file_token_count: Optional[int]) -> str:
        wrapper_start = f'<file path="{xml_escape(relative_path)}"'
        if file_token_count is not None:
            wrapper_start += f' tokens="{file_token_count}"'
        wrapper_start += ">\n"
        return wrapper_start

    def format_content(self, content: str) -> str:
        return xml_escape(content)

    def format_end(self, file_token_count: Optional[int]) -> str:
        return "</file>\n"

    def get_file_extension(self) -> str:
        return ".xml"
