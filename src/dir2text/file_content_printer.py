from typing import Literal, Iterator, Tuple, Optional
from .file_system_tree import FileSystemTree
from .token_counter import TokenCounter

WrapperFormat = Literal["xml", "json"]


class FileContentPrinter:
    def __init__(
        self, fs_tree: FileSystemTree, wrapper_format: WrapperFormat = "xml", tokenizer: Optional[TokenCounter] = None
    ):
        self.fs_tree = fs_tree
        self.wrapper_format = wrapper_format
        self.tokenizer = tokenizer

    def yield_file_contents(self) -> Iterator[Tuple[str, str, Iterator[str]]]:
        """
        Yields tuples of (file_path, relative_path, content_iterator) for all files in the tree.
        The content_iterator yields lines of the file content, including wrapper start and end.
        """
        for file_path, relative_path in self.fs_tree.iterate_files():
            yield file_path, relative_path, self._yield_wrapped_content(file_path, relative_path)

    def _yield_wrapped_content(self, file_path: str, relative_path: str) -> Iterator[str]:
        """
        Yields wrapped content of a file line by line, including wrapper start and end.
        """
        if self.wrapper_format == "xml":
            yield from self._yield_xml_content(file_path, relative_path)
        else:  # JSON format
            yield from self._yield_json_content(file_path, relative_path)

    def _process_file_content(self, file_path: str, count: bool = True) -> Iterator[Tuple[str, int]]:
        """
        Process file content in chunks, yielding (chunk, token_count) tuples.
        If count is False, token_count will always be 0.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                leftover = ""
                while True:
                    chunk = leftover + file.read(65536)  # Read in 64KB chunks
                    if not chunk:
                        break

                    last_whitespace = max(chunk.rfind(" "), chunk.rfind("\n"), chunk.rfind("\t"))

                    if last_whitespace == -1:
                        yield_chunk = chunk
                        leftover = ""
                    else:
                        yield_chunk = chunk[: last_whitespace + 1]
                        leftover = chunk[last_whitespace + 1 :]  # noqa: E203

                    token_count = self.tokenizer.count_tokens(yield_chunk) if self.tokenizer and count else 0

                    yield yield_chunk, token_count

                if leftover:
                    token_count = self.tokenizer.count_tokens(leftover) if self.tokenizer and count else 0
                    yield leftover, token_count
        except Exception as e:
            error_message = f"Error reading file {file_path}: {str(e)}\n"
            yield error_message, 0  # Error messages are not counted

    def _yield_xml_content(self, file_path: str, relative_path: str) -> Iterator[str]:
        # First pass: count tokens if tokenizer is available
        file_token_count = sum(
            token_count for _, token_count in self._process_file_content(file_path, count=bool(self.tokenizer))
        )

        wrapper_start = f'<file path="{relative_path}"'
        if self.tokenizer:
            wrapper_start += f' tokens="{file_token_count}"'
        wrapper_start += ">\n"

        if self.tokenizer:
            self.tokenizer.count_tokens(wrapper_start)
        yield wrapper_start

        # Second pass: yield content (without counting tokens again)
        for chunk, _ in self._process_file_content(file_path, count=False):
            yield chunk

        wrapper_end = "</file>\n"
        if self.tokenizer:
            self.tokenizer.count_tokens(wrapper_end)
        yield wrapper_end

    def _yield_json_content(self, file_path: str, relative_path: str) -> Iterator[str]:
        wrapper_start = f'{{"path": "{relative_path}"'
        if self.tokenizer:
            wrapper_start += ', "tokens": '
        wrapper_start += ', "content": "'

        if self.tokenizer:
            self.tokenizer.count_tokens(wrapper_start)
        yield wrapper_start

        file_token_count = 0
        for chunk, token_count in self._process_file_content(file_path, count=bool(self.tokenizer)):
            escaped_chunk = chunk.replace('"', '\\"').replace("\n", "\\n")
            yield escaped_chunk
            file_token_count += token_count

        wrapper_end = '"'
        if self.tokenizer:
            wrapper_end += f', "tokens": {file_token_count}'
        wrapper_end += "}"

        if self.tokenizer:
            self.tokenizer.count_tokens(wrapper_end)
        yield wrapper_end
