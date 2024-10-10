from typing import Literal, Iterator, Tuple
from .file_system_tree import FileSystemTree

WrapperFormat = Literal["xml", "json"]


class FileContentPrinter:
    def __init__(self, fs_tree: FileSystemTree, wrapper_format: WrapperFormat = "xml"):
        self.fs_tree = fs_tree
        self.wrapper_format = wrapper_format

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
        yield self._get_wrapper_start(relative_path) + "\n"

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    yield line
        except Exception as e:
            yield f"Error reading file {relative_path}: {str(e)}\n"

        yield self._get_wrapper_end(relative_path) + "\n"

    def _get_wrapper_start(self, filename: str) -> str:
        if self.wrapper_format == "xml":
            return f'<file path="{filename}">'
        elif self.wrapper_format == "json":
            return f'{{"path": "{filename}", "content": "'

    def _get_wrapper_end(self, filename: str) -> str:
        if self.wrapper_format == "xml":
            return "</file>"
        elif self.wrapper_format == "json":
            return '"}'
