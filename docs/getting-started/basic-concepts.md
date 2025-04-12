# Basic Concepts

## Overview

dir2text is designed to convert directory structures into text representations suitable for Large Language Models (LLMs) and other analysis tasks. It combines several key features:

- Directory tree visualization
- File content extraction
- GitIgnore-style exclusion rules
- Optional token counting for LLMs
- Memory-efficient streaming processing
- Symbolic link representation and handling

## Directory Trees

### Structure Representation

dir2text creates a tree representation of your directory structure:

```
project/
├── src/
│   ├── main.py
│   └── utils/
│       └── helpers.py
├── docs → ./README.md [symlink]
└── README.md
```

Key features:
- Directories marked with trailing `/`
- Files shown without trailing markers
- Symbolic links marked with an arrow (`→`) and target path
- Sorted alphabetically (directories first, then files)
- Unicode support for file and directory names

### Tree Building

Trees are built with these characteristics:
- Lazy loading (built only when accessed)
- Memory-efficient processing
- Proper symlink handling and loop detection
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
<symlink path="docs" target="./README.md" />
```

2. JSON Format:
```json
{"type": "file", "path": "src/main.py", "content": "def main():\n    print(\"Hello, World!\")\n", "tokens": 42}
{"type": "symlink", "path": "docs", "target": "./README.md"}
```

### Content Handling

Content processing features:
- Stream-based processing
- Proper escaping for output format
- UTF-8 encoding
- Constant memory usage

## Symbolic Link Handling

### Overview

dir2text offers two modes for handling symbolic links:

1. **Default Mode**: Symbolic links are represented as symlinks (not followed)
   - Links appear in tree visualization with their target
   - Links are included in content output as symlink elements
   - No duplicate content

2. **Follow Mode** (`-L` option): Symbolic links are followed like directories
   - Target contents are processed as if they were part of the tree
   - Symlink loops are detected and prevented
   - Files may appear multiple times through different paths

### Representation in Tree Visualization

**Default Mode (without `-L`):**
```
project/
├── src/
│   └── main.py
└── link_to_src → ./src/ [symlink]
```

**Follow Mode (with `-L`):**
```
project/
├── src/
│   └── main.py
└── link_to_src/
    └── main.py
```

### Representation in Content Output

**Default Mode (without `-L`):**
```xml
<file path="src/main.py">
def main():
    print("Hello, World!")
</file>
<symlink path="link_to_src" target="./src/" />
```

**Follow Mode (with `-L`):**
```xml
<file path="src/main.py">
def main():
    print("Hello, World!")
</file>
<file path="link_to_src/main.py">
def main():
    print("Hello, World!")
</file>
```

### Loop Protection

Both modes include protection against symbolic link loops:
- Loops are detected using device ID and inode number tracking
- When a loop is detected, it's marked and traversal stops at that point
- This prevents infinite recursion regardless of symlink following mode

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
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules

# Create exclusion rules
rules = GitIgnoreExclusionRules()
rules.load_rules(".gitignore")

# Create analyzer
analyzer = StreamingDir2Text(
    "/path/to/project", 
    exclusion_rules=rules,
    follow_symlinks=False  # Default behavior, don't follow symlinks
)

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
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules

# Create exclusion rules
rules = GitIgnoreExclusionRules()
rules.load_rules(".gitignore")

# Ignore permission errors (default)
tree = FileSystemTree(
    "/path/to/project",
    exclusion_rules=rules,
    permission_action=PermissionAction.IGNORE
)

# Raise permission errors
tree = FileSystemTree(
    "/path/to/project",
    exclusion_rules=rules,
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
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules

# Create exclusion rules
rules = GitIgnoreExclusionRules()
rules.load_rules(".gitignore")

# Process with XML output
analyzer = StreamingDir2Text(
    "/path/to/project",
    exclusion_rules=rules,
    output_format="xml"
)

# Stream content
for chunk in analyzer.stream_contents():
    print(chunk, end='')
```

### LLM Preparation
```python
from dir2text import Dir2Text
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules

# Create exclusion rules
rules = GitIgnoreExclusionRules()
rules.load_rules(".gitignore")

# Full processing with token counting
analyzer = Dir2Text(
    "/path/to/project",
    exclusion_rules=rules,
    output_format="json",
    tokenizer_model="gpt-4"
)

# Access processed content
print(analyzer.content_string)
print(f"Total tokens: {analyzer.token_count}")
```

### Processing with Symlinks
```python
from dir2text import Dir2Text

# Default mode - represent symlinks without following
analyzer = Dir2Text("/path/to/project")

# Follow mode - follow symlinks and include their targets' content
analyzer_follow = Dir2Text(
    "/path/to/project",
    follow_symlinks=True
)

# Print symlink count (only available in default mode)
print(f"Symlinks: {analyzer.symlink_count}")
```