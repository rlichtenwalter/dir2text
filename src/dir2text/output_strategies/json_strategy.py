import json
from typing import Optional

from .base_strategy import OutputStrategy


class JSONOutputStrategy(OutputStrategy):
    def __init__(self):
        self.encoder = json.JSONEncoder()
        self.is_first_chunk = True

    def format_start(self, relative_path: str, file_token_count: Optional[int]) -> str:
        data = {"path": relative_path}
        if file_token_count is not None:
            data["tokens"] = str(file_token_count)

        # Start the JSON object and the content field
        start = "{"
        for chunk in self.encoder.iterencode(data):
            start += chunk
        start = start.rstrip("}")  # Remove the closing brace
        if not start.endswith(","):
            start += ","
        start += '"content":"'

        return start

    def format_content(self, content: str) -> str:
        # Use the encoder to properly escape the content
        escaped = ""
        for chunk in self.encoder.iterencode(content):
            escaped += chunk
        # Remove the surrounding quotes added by the encoder
        escaped = escaped[1:-1]
        return escaped

    def format_end(self, file_token_count: Optional[int]) -> str:
        end = '"'
        if file_token_count is not None:
            end += f',"tokens":{file_token_count}'
        end += "}"
        return end

    def get_file_extension(self) -> str:
        return ".json"
