from abc import ABC, abstractmethod
from typing import Optional


class OutputStrategy(ABC):
    @abstractmethod
    def format_start(self, relative_path: str, file_token_count: Optional[int] = None) -> str:
        """Format the start of a file's content representation."""
        pass

    @abstractmethod
    def format_content(self, content: str) -> str:
        """Format the main content of a file."""
        pass

    @abstractmethod
    def format_end(self, file_token_count: Optional[int] = None) -> str:
        """Format the end of a file's content representation."""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this output format."""
        pass
