import sys
from typing import Literal
from .file_system_tree import FileSystemTree

WrapperFormat = Literal["xml", "json"]


class FileContentPrinter:
    def __init__(self, fs_tree: FileSystemTree, wrapper_format: WrapperFormat = "xml"):
        self.fs_tree = fs_tree
        self.wrapper_format = wrapper_format
        self.is_first_file = True

    def print_all_file_contents(self):
        for file_path, relative_path in self.fs_tree.iterate_files():
            if not self.is_first_file:
                print()  # Print newline between files, but not before the first file
            else:
                self.is_first_file = False
            self._print_file_content(file_path, relative_path)

    def _print_file_content(self, file_path: str, relative_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                self._print_wrapper_start(relative_path)
                for line in file:
                    print(line, end="")
                self._print_wrapper_end(relative_path)
        except Exception as e:
            print(f"Error reading file {relative_path}: {str(e)}", file=sys.stderr)

    def _print_wrapper_start(self, filename: str):
        if self.wrapper_format == "xml":
            print(f'<file path="{filename}">')
        elif self.wrapper_format == "json":
            print(f'{{"path": "{filename}", "content": "')

    def _print_wrapper_end(self, filename: str):
        if self.wrapper_format == "xml":
            print("</file>")
        elif self.wrapper_format == "json":
            print('"}')
