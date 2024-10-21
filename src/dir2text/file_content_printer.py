from typing import Iterator, Optional, Tuple, Union

from .file_system_tree import FileSystemTree
from .output_strategies.base_strategy import OutputStrategy
from .output_strategies.json_strategy import JSONOutputStrategy
from .output_strategies.xml_strategy import XMLOutputStrategy
from .token_counter import TokenCounter


class FileContentPrinter:
    def __init__(
        self,
        fs_tree: FileSystemTree,
        output_format: Union[str, OutputStrategy] = "xml",
        tokenizer: Optional[TokenCounter] = None,
    ):
        self.fs_tree = fs_tree
        self.tokenizer = tokenizer

        if isinstance(output_format, str):
            output_format = output_format.lower()
            if output_format == "xml":
                self.output_strategy: OutputStrategy = XMLOutputStrategy()
            elif output_format == "json":
                self.output_strategy = JSONOutputStrategy()
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
        elif isinstance(output_format, OutputStrategy):
            self.output_strategy = output_format
        else:
            raise TypeError("output_format must be either a string or an OutputStrategy instance")

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
        file_token_count = None
        if self.tokenizer:
            file_token_count = sum(token_count for _, token_count in self._process_file_content(file_path, count=True))

        yield self.output_strategy.format_start(relative_path, file_token_count)

        for chunk, _ in self._process_file_content(file_path, count=False):
            yield self.output_strategy.format_content(chunk)

        yield self.output_strategy.format_end(file_token_count)

    def _process_file_content(self, file_path: str, count: bool = False) -> Iterator[Tuple[str, int]]:
        """
        Process file content in chunks, yielding (chunk, token_count) tuples.
        If count is False, token_count will always be 0.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                while True:
                    chunk = file.read(65536)  # Read in 64KB chunks
                    if not chunk:
                        break

                    token_count = self.tokenizer.count_tokens(chunk) if self.tokenizer and count else 0
                    yield chunk, token_count

        except Exception as e:
            error_message = f"Error reading file {file_path}: {str(e)}\n"
            yield error_message, 0  # Error messages are not counted

    def get_output_file_extension(self) -> str:
        """
        Returns the file extension for the current output format.
        """
        return self.output_strategy.get_file_extension()
