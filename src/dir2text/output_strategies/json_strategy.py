import json
from typing import Optional

from .base_strategy import OutputStrategy


class JSONOutputStrategy(OutputStrategy):
    def __init__(self) -> None:
        self.encoder = json.JSONEncoder()
        self.token_count: Optional[int] = None

    def format_start(self, relative_path: str, file_token_count: Optional[int] = None) -> str:
        data = {"path": relative_path}
        self.token_count = file_token_count

        # Start the JSON object and the content field
        start = self.encoder.encode(data)
        start = start.rstrip("}")  # Remove the closing brace
        start += ', "content": "'

        return start

    def format_content(self, content: str) -> str:
        # Since format_content may be called for each chunk of data in a stream,
        # we need to escape each chunk for JSON but without the surrounding quotes
        # that would normally be added by json encoding
        return self.encoder.encode(content)[1:-1]  # Remove the surrounding quotes

    def format_end(self, file_token_count: Optional[int] = None) -> str:
        end = '"'
        if file_token_count is not None:
            if self.token_count is not None:
                if self.token_count != file_token_count:
                    raise ValueError(
                        "Non-matching token counts supplied at format_start and format_end: "
                        + f"'{self.token_count}' and '{file_token_count}'"
                    )
            self.token_count = file_token_count
        if self.token_count is not None:
            end += f', "tokens": {self.token_count}'
        end += "}"
        return end

    def get_file_extension(self) -> str:
        return ".json"
