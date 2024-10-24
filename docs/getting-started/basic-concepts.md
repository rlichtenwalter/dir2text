# Basic Concepts

## Overview

dir2text is designed to convert directory structures into text representations suitable for Large Language Models (LLMs) and other analysis tasks. It combines several key features:

- Directory tree visualization
- File content extraction
- GitIgnore-style exclusion rules
- Optional token counting for LLMs
- Memory-efficient streaming processing

## Directory Trees

### Structure Representation

dir2text creates a tree representation of your directory structure:

```
project/
├── src/
│   ├── main.py
│   └── utils/
│       └── helpers.py
└── README.md
```

Key features:
- Directories marked with trailing `/`
- Files shown without trailing markers
- Sorted alphabetically (directories first, then files)
- Unicode support for file and directory names

### Tree Building

Trees are built with these characteristics:
- Lazy loading (built only when accessed)
- Memory-efficient processing
- Proper symlink handling
- Permission error handling
- Consistent sorting

## Content Processing

### Output Formats

1. XML Format (default):
```xml
<file path="src/main.py" tokens="42">
def main():
    print("Hello, World!")
</file>
```

2. JSON Format:
```json
{
  "path": "src/main.py",
  "content": "def main():\n    print(\"Hello, World!\")\n",
  "tokens": 42
}
```

### Content Handling

Content processing features:
- Stream-based processing
- Proper escaping for output format
- UTF-8 encoding
- Constant memory usage

## Exclusion Rules

### Overview

Exclusion rules filter out files and directories you don't want to process:
- Built artifacts
- Cache directories
- Version control files
- Binary files

### GitIgnore Support

dir2text uses standard .gitignore pattern syntax:

```gitignore
# Python artifacts
__pycache__/
*.pyc
*$py.class

# Build directories
build/
dist/
```

Supported patterns:
- Basic globs (`*`, `?`)
- Directory markers (`dir/`)
- Negation (`!important.txt`)
- Comments (`# comment`)

## Token Counting

### Purpose

Token counting helps manage LLM context limits by:
- Tracking token usage
- Providing accurate counts
- Supporting different models
- Maintaining streaming efficiency

### Models and Encodings

Token counting uses tiktoken's encodings:
- GPT-4 models (cl100k_base encoding)
- GPT-3.5-Turbo models (cl100k_base encoding)
- Text Davinci models (p50k_base encoding)

```python
from dir2text.token_counter import TokenCounter

counter = TokenCounter(model="gpt-4")
result = counter.count("Hello, world!")
print(f"Tokens: {result.tokens}")
```

## Memory Management

### Streaming Design

dir2text uses streaming to maintain constant memory usage:

```python
from dir2text import StreamingDir2Text

# Create analyzer
analyzer = StreamingDir2Text("/path/to/project")

# Process tree (memory-efficient)
for line in analyzer.stream_tree():
    print(line, end='')

# Process contents (memory-efficient)
for chunk in analyzer.stream_contents():
    print(chunk, end='')
```

Key features:
- Constant memory usage
- Chunk-based processing
- No full content loading

## Permission Handling

dir2text provides two permission handling modes:

```python
from dir2text import FileSystemTree
from dir2text.file_system_tree import PermissionAction

# Ignore permission errors (default)
tree = FileSystemTree(
    "/path/to/project",
    permission_action=PermissionAction.IGNORE
)

# Raise permission errors
tree = FileSystemTree(
    "/path/to/project",
    permission_action=PermissionAction.RAISE
)
```

Behaviors:
- IGNORE: Skip inaccessible items
- RAISE: Stop on permission errors

## Common Usage Patterns

### Basic Tree Visualization
```python
from dir2text import FileSystemTree

# Create and print tree
tree = FileSystemTree("/path/to/project")
print(tree.get_tree_representation())
```

### Content Processing
```python
from dir2text import StreamingDir2Text

# Process with XML output
analyzer = StreamingDir2Text(
    "/path/to/project",
    output_format="xml"
)

# Stream content
for chunk in analyzer.stream_contents():
    print(chunk, end='')
```

### LLM Preparation
```python
from dir2text import Dir2Text

# Full processing with token counting
analyzer = Dir2Text(
    "/path/to/project",
    output_format="json",
    tokenizer_model="gpt-4"
)

# Access processed content
print(analyzer.content_string)
print(f"Total tokens: {analyzer.token_count}")
```