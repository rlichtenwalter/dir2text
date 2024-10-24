# Development Guide

## Setting Up Development Environment

### Prerequisites

- Python 3.9.1 or later
- Poetry for dependency management
- Git for version control
- A Rust compiler and Cargo (for token counting development)

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/rlichtenwalter/dir2text.git
cd dir2text
```

2. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
# Install all dependencies including development ones
poetry install --with dev

# Include token counting support
poetry install --with dev -E token_counting
```

4. Install pre-commit hooks:
```bash
poetry run pre-commit install
```

## Development Workflow

### Branch Management

1. Create a feature branch:
```bash
# For new features
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b fix/bug-description

# For documentation
git checkout -b docs/topic-name
```

2. Keep your branch up to date:
```bash
git fetch origin
git rebase origin/main
```

### Code Quality

Run quality checks frequently during development:

```bash
# Format code (black + isort)
poetry run tox -e format

# Run linters
poetry run tox -e lint

# Type checking
poetry run tox -e typecheck

# Run tests
poetry run tox -e test
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_file_system_tree.py

# Run specific test
poetry run pytest tests/test_file_system_tree.py::test_function_name

# Run with coverage
poetry run tox -e coverage
```

## Project Structure

```
dir2text/
├── src/
│   └── dir2text/
│       ├── exclusion_rules/    # Exclusion rule implementations
│       ├── io/                 # I/O utilities
│       ├── output_strategies/  # Output formatting
│       └── *.py               # Core modules
├── tests/                     # Test directory (mirrors src/dir2text/)
├── docs/                      # Documentation
└── pyproject.toml            # Project configuration
```

## Development Standards

### Code Style

1. Follow PEP 8 with these adjustments:
```python
# Maximum line length is 120 characters
from typing import (
    Dict, List, Optional,  # Aligned wrapped imports
    Set, Tuple, Union
)

# Use trailing commas in multiline collections
my_list = [
    1,
    2,
    3,  # Note trailing comma
]
```

2. Use type hints:
```python
from typing import Optional, Sequence

def process_items(
    items: Sequence[str],
    separator: Optional[str] = None
) -> str:
    """Process items with an optional separator."""
    sep = separator or ','
    return sep.join(items)
```

### Documentation

1. Module Documentation:
```python
"""Module description.

This module provides functionality for... It includes classes for...
and utilities that help with...

Example:
    Basic usage example:
    >>> from dir2text import FileSystemTree
    >>> tree = FileSystemTree("path")
    >>> print(tree.get_tree_representation())
"""
```

2. Class Documentation:
```python
class ExampleClass:
    """Class purpose and behavior.
    
    Detailed description of the class, its behavior, and important
    notes about usage.
    
    Attributes:
        attr_name: Description of attribute
        
    Example:
        >>> obj = ExampleClass()
        >>> obj.method()
    """
```

3. Method Documentation:
```python
def example_method(self, param: str) -> bool:
    """Short description.

    Detailed description of what the method does, important
    notes about usage, and any special behaviors.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this is raised
        
    Example:
        >>> obj.example_method("test")
        True
    """
```

### Error Handling

1. Exception Hierarchy:
```python
# In exceptions.py
class TokenizerError(Dir2TextError):
    """Base class for tokenizer errors."""

class TokenizerNotAvailableError(TokenizerError):
    """Raised when tokenizer is not installed."""
```

## Testing Guidelines

### Test Organization

1. Test File Structure:
```python
"""Tests for module_name."""

import pytest
from dir2text import TestedClass

@pytest.fixture
def test_instance():
    """Provide a test instance."""
    return TestedClass()

class TestTestedClass:
    """Tests for TestedClass."""
    
    def test_basic_operation(self, test_instance):
        """Test basic operations."""
        result = test_instance.operation()
        assert result == expected
    
    def test_error_conditions(self, test_instance):
        """Test error handling."""
        with pytest.raises(ValueError):
            test_instance.invalid_operation()
```

2. Test Categories:
```python
# Unit tests (test_*.py)
def test_individual_function():
    assert function(input) == expected
```

### Writing Tests

1. Arrange-Act-Assert Pattern:
```python
def test_file_processing():
    # Arrange
    content = "test content"
    test_file = tmp_path / "test.txt"
    test_file.write_text(content)
    
    # Act
    processor = FileProcessor(test_file)
    result = processor.process()
    
    # Assert
    assert result.content == content
    assert result.lines == 1
```

2. Using Fixtures:
```python
@pytest.fixture
def test_directory(tmp_path):
    """Create a test directory structure."""
    # Create files and directories
    (tmp_path / "src").mkdir()
    (tmp_path / "src/main.py").write_text("print('test')")
    return tmp_path

def test_tree_building(test_directory):
    tree = FileSystemTree(test_directory)
    assert tree.get_file_count() == 1
```

## Release Process

1. Update Version:
   - Update version in pyproject.toml
   - Update CHANGELOG.md

2. Create Release Commit:
```bash
# Update version
poetry version patch  # or minor, major

# Update changelog
git add pyproject.toml CHANGELOG.md
git commit -m "Release version X.Y.Z"
```

3. Tag Release:
```bash
git tag -a vX.Y.Z -m "Version X.Y.Z"
git push origin vX.Y.Z
```

4. Build and Publish:
```bash
# Build distribution
poetry build

# Publish to PyPI
poetry publish
```