# dir2text Documentation

`dir2text` is a Python library and command-line tool for converting directory structures into human and machine-readable text representations. It's particularly useful for preparing codebases for Large Language Model (LLM) analysis, creating documentation, or archiving directory structures with content.

## Quick Start

```bash
# Install with pip
pip install dir2text

# Basic usage - output directory structure and contents
dir2text /path/to/directory

# Output as JSON instead of XML
dir2text /path/to/directory --format json

# Exclude files based on .gitignore patterns
dir2text /path/to/directory -e .gitignore

# Enable token counting (requires token_counting extra)
dir2text /path/to/directory --tokenizer gpt-4
```

## Key Features

- Directory tree visualization similar to the Unix `tree` command
- Complete file content extraction with XML or JSON formatting
- GitIgnore-style pattern exclusions
- Optional token counting for LLM context management (with `token_counting` extra)
- Python API for programmatic use

## Common Use Cases

1. **LLM Code Analysis**
   ```bash
   dir2text /path/to/project -e .gitignore --tokenizer gpt-4 > project.txt
   ```

2. **Project Documentation**
   ```bash
   dir2text /path/to/project --no-contents > structure.txt
   ```

3. **Directory Archiving**
   ```bash
   dir2text /path/to/project --format json > archive.json
   ```

## Basic Python Usage

```python
from dir2text import FileSystemTree
from dir2text.file_content_printer import FileContentPrinter
from dir2text.output_strategies import XMLOutputStrategy

# Create a file system tree
fs_tree = FileSystemTree("/path/to/directory")

# Print directory structure
print(fs_tree.get_tree_representation())

# Print file contents with XML formatting
printer = FileContentPrinter(fs_tree, output_format="xml")
for abs_path, rel_path, content_iter in printer.yield_file_contents():
    for chunk in content_iter:
        print(chunk, end='')
```