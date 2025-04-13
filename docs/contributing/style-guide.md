# Style Guide

## Code Formatting

### Basic Rules

- Line length: 120 characters maximum
- Indentation: 4 spaces (no tabs)
- UTF-8 encoding for all Python files
- Two blank lines between top-level definitions
- One blank line between method definitions
- No trailing whitespace

### Tool Configuration

```toml
# pyproject.toml
[tool.black]
line-length = 120
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
line_length = 120

[tool.flake8]
max-line-length = 120
extend-select = ["B", "C", "E", "F", "W", "B950"]
```

### Import Organization

```python
# Standard library imports
import os
from pathlib import Path
from typing import Optional, Union

# Third-party imports
import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# Local imports
from dir2text.exceptions import TokenizationError
from dir2text.file_system_tree import FileSystemTree, PermissionAction
```

### Alignment and Wrapping

```python
# Function arguments
def long_function_name(
    arg1: str,
    arg2: Optional[str],
    *args: str,
    kwarg1: int = 0,
    kwarg2: str = "default",
) -> None:
    pass

# Lists, tuples, and sets
long_list = [
    item1,
    item2,
    item3,
]

# Dictionaries
config = {
    "key1": "value1",
    "key2": "value2",
    "key3": "value3",
}

# Multiple context managers
with (
    open("file1.txt") as f1,
    open("file2.txt") as f2
):
    pass
```

## Naming Conventions

### General Rules

- Package names: `lowercase`
- Module names: `lowercase_with_underscores`
- Class names: `PascalCase`
- Function/method names: `snake_case`
- Constants: `UPPER_CASE_WITH_UNDERSCORES`
- Variables: `snake_case`
- Type variables: `PascalCase` (prefer single letters like `T`, `U`)

### Examples

```python
# Module name: file_system_tree.py
from os import PathLike
from typing import Optional, Union, TypeVar

# Constants
DEFAULT_CHUNK_SIZE = 8192
MAX_TOKEN_LIMIT = 150000

# Type variables
T = TypeVar('T')
PathType = Union[str, PathLike[str]]

# Classes
class FileSystemTree:
    """Tree representation of filesystem."""
    
    def __init__(self, root_path: PathType) -> None:
        # Instance variables
        self.root_path = root_path
        self._cached_data: Optional[dict] = None

# Functions
def process_directory(path: PathType) -> None:
    """Process a directory."""
    pass
```

## Type Hints

### Basic Usage

```python
from typing import Dict, List, Optional, Sequence, Union

# Function arguments and return types
def process_items(
    items: Sequence[str],
    separator: Optional[str] = None,
) -> str:
    """Process items with separator."""
    return (separator or ',').join(items)

# Variable annotations
names: List[str] = []
config: Dict[str, Union[str, int]] = {}

# Class attributes
class Configuration:
    debug: bool = False
    retry_count: int = 3
    paths: List[Path] = []
```

### Advanced Types

```python
from typing import Callable, Iterator, Protocol, TypeVar

T = TypeVar('T')

class Processor(Protocol):
    """Protocol for content processors."""
    
    def process(self, content: str) -> str:
        """Process content."""
        ...

def process_with_callback(
    items: Sequence[T],
    callback: Callable[[T], None],
) -> None:
    """Process items with callback."""
    for item in items:
        callback(item)

def generate_items() -> Iterator[str]:
    """Generate items."""
    yield from []
```

## Documentation

### Module Documentation

```python
"""File system tree representation with exclusion support.

This module provides classes and utilities for building and manipulating
tree representations of directory structures. Key features include:

- Lazy tree building
- Configurable file exclusion
- Memory-efficient traversal
- Permission error handling

Example:
    Basic usage:
    >>> from dir2text import FileSystemTree
    >>> tree = FileSystemTree("/path/to/directory")
    >>> print(tree.get_tree_representation())
"""

from typing import Optional

# Rest of module...
```

### Class Documentation

```python
class StreamingDir2Text:
    """Memory-efficient directory content analyzer.

    This class provides a streaming interface for processing directory
    content, ensuring constant memory usage regardless of directory size.

    The streaming design enables:
    - Processing of large directories
    - Memory-efficient content handling
    - Incremental token counting
    - Progressive output generation

    Attributes:
        directory: Path to the root directory
        exclude_file: Optional path to exclusion rules file
        streaming_complete: Whether all streaming is finished
        
    Example:
        >>> analyzer = StreamingDir2Text("src")
        >>> for line in analyzer.stream_tree():
        ...     print(line, end='')
    """
```

### Method Documentation

```python
def process_content(
    self,
    content: str,
    *,
    normalize: bool = False,
) -> str:
    """Process content with optional normalization.
    
    This method handles content processing while ensuring proper
    character encoding and normalization.
    
    Args:
        content: The content to process
        normalize: Whether to normalize whitespace (default: False)
        
    Returns:
        The processed content string
        
    Raises:
        ValueError: If content contains invalid characters
        UnicodeError: If content cannot be encoded
        
    Example:
        >>> processor.process_content("  text  ", normalize=True)
        'text'
    """
```

### Property Documentation

```python
@property
def token_count(self) -> int:
    """Total number of tokens processed.
    
    This count accumulates during streaming operations and represents
    the total number of tokens processed so far.
    
    Returns:
        Current token count
        
    Note:
        Returns 0 if token counting is disabled
        
    Example:
        >>> analyzer.token_count
        150
    """
    return self._total_tokens
```

## Error Handling

### Exception Definition

```python
class Dir2TextError(Exception):
    """Base exception for dir2text."""

class TokenizerError(Dir2TextError):
    """Base class for tokenizer errors."""
    
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize with optional details."""
        self.details = details
        super().__init__(message)

class TokenizerNotAvailableError(TokenizerError):
    """Raised when tokenizer is not installed."""
```

### Error Handling Patterns

```python
def process_safely(self, path: str) -> None:
    """Process with comprehensive error handling."""
    try:
        self._process(path)
    except FileNotFoundError as e:
        # Add context to filesystem errors
        raise FileNotFoundError(
            f"Failed to process {path}: {e}"
        ) from e
    except PermissionError as e:
        if self.permission_action == PermissionAction.RAISE:
            raise
        # Log and continue
        logging.warning("Skipping %s: %s", path, e)
    except UnicodeError as e:
        # Handle encoding issues
        logging.error(
            "Failed to decode %s: %s",
            path,
            e,
            exc_info=True
        )
```

## Testing

### Test Documentation

```python
def test_file_system_tree_initialization(temp_directory):
    """Test basic initialization of FileSystemTree.
    
    This test verifies that:
    1. The tree is initialized with correct path
    2. The tree is not built until accessed
    3. Attributes are properly set
    """
    fs_tree = FileSystemTree(str(temp_directory))
    assert fs_tree.root_path == str(temp_directory)
    assert fs_tree._tree is None
```

### Test Organization

```python
class TestFileSystemTree:
    """Tests for FileSystemTree class."""
    
    class TestInitialization:
        """Initialization tests."""
        
        def test_basic_init(self):
            """Test basic initialization."""
    
    class TestTreeBuilding:
        """Tree building tests."""
        
        def test_lazy_building(self):
            """Test lazy tree building."""
```

## Next Steps

- Read [Development Guide](development.md) for setup information
- Check [Testing Guide](testing.md) for test writing
- See [API Documentation](../api/core.md) for code examples