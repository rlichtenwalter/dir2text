# dir2text

A Python library and command-line tool for expressing directory structures and file contents in formats suitable for Large Language Models (LLMs). It combines directory tree visualization with file contents in a memory-efficient, streaming format.

## Features

- Tree-style directory structure visualization
- Complete file contents with proper escaping
- Memory-efficient streaming processing
- Multiple output formats (XML, JSON)
- Easy extensibility for new formats
- Support for exclusion patterns (e.g., .gitignore rules)
- Proper symbolic link handling and loop detection
- Optional token counting for LLM context management
- Statistics reporting with configurable output destination
- Safe handling of large files and directories

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management. We recommend using Poetry for the best development experience, but we also provide traditional pip installation.

### Using Poetry (Recommended)

1. First, [install Poetry](https://python-poetry.org/docs/#installation) if you haven't already.
2. Install dir2text:
   ```bash
   poetry add dir2text
   ```

### Using pip

```bash
pip install dir2text
```

### Optional Features

Install with token counting support (for LLM context management):
```bash
# With Poetry
poetry add "dir2text[token_counting]"

# With pip
pip install "dir2text[token_counting]"
```

**Note:** The `token_counting` feature requires the `tiktoken` package, which needs a Rust compiler (e.g., `rustc`) and Cargo to be available during installation.

## Usage

### Command Line Interface

Basic usage:
```bash
dir2text /path/to/project

# Show version information
dir2text --version

# Exclude files matching patterns from one or more exclusion files
dir2text -e .gitignore /path/to/project
dir2text -e .gitignore -e .npmignore -e custom-ignore /path/to/project

# Exclude files with direct patterns
dir2text -i "*.pyc" -i "node_modules/" /path/to/project

# Enable token counting for LLM context management
dir2text -c /path/to/project

# Generate JSON output and save to file
dir2text -f json -o output.json /path/to/project

# Follow symbolic links
dir2text -L /path/to/project

# Skip tree or content sections
dir2text -T /path/to/project     # Skip tree visualization
dir2text -C /path/to/project     # Skip file contents
```

### Symbolic Link Handling

By default, symbolic links are represented as symlinks without following them:

```bash
dir2text /path/to/project
```

This shows symlinks clearly marked with their targets in the tree output, and as separate elements in content output.

To follow symbolic links during traversal (similar to Unix `find -L`):

```bash
dir2text -L /path/to/project
```

This includes the content that symlinks point to, while still protecting against symlink loops.

### Statistics Reporting

Dir2text can generate statistics about the processed directory including file counts, line counts, and optionally token counts. You can control where these statistics are displayed:

```bash
# Print statistics to stderr (default)
dir2text -s stderr /path/to/project

# Print statistics to stdout
dir2text -s stdout /path/to/project

# Include statistics in the output file
dir2text -s file -o output.txt /path/to/project

# Show token counts in statistics by enabling token counting
dir2text -s -c /path/to/project
```

Statistics include counts of directories, files, symlinks, lines, and characters. Token counts are only included when token counting is enabled with the `-c` option.

Note that token counting (`-c`) and statistics reporting (`-s`) are separate concerns:
- `-c` enables token counting and embeds token counts in the output markup
- `-s` controls whether statistics are generated and where they are displayed

### Python API

Basic usage:
```python
from dir2text import StreamingDir2Text
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules

# Create exclusion rules (optional)
rules = GitIgnoreExclusionRules()
rules.add_rule("*.pyc")  # Add rules directly
# OR load from files
rules.load_rules(".gitignore")

# Initialize the analyzer
analyzer = StreamingDir2Text("path/to/project", exclusion_rules=rules)

# Stream the directory tree
for line in analyzer.stream_tree():
    print(line, end='')

# Stream file contents
for chunk in analyzer.stream_contents():
    print(chunk, end='')

# Get metrics
print(f"Processed {analyzer.file_count} files in {analyzer.directory_count} directories")
print(f"Found {analyzer.symlink_count} symbolic links")
```

Memory-efficient processing with token counting:
```python
from dir2text import StreamingDir2Text
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules

# Create exclusion rules from multiple files
rules = GitIgnoreExclusionRules()
rules.load_rules(".gitignore")
rules.load_rules(".npmignore")
rules.add_rule("custom.ignore")

# Initialize with options
analyzer = StreamingDir2Text(
    directory="path/to/project",
    exclusion_rules=rules,
    output_format="json",
    tokenizer_model="gpt-4",
    follow_symlinks=False  # Default behavior, don't follow symlinks
)

# Process content incrementally
with open("output.json", "w") as f:
    for line in analyzer.stream_tree():
        f.write(line)
    for chunk in analyzer.stream_contents():
        f.write(chunk)

# Print statistics
print(f"Files: {analyzer.file_count}")
print(f"Directories: {analyzer.directory_count}")
print(f"Symlinks: {analyzer.symlink_count}")
print(f"Lines: {analyzer.line_count}")
print(f"Tokens: {analyzer.token_count}")
print(f"Characters: {analyzer.character_count}")
```

Immediate processing (for smaller directories):
```python
from dir2text import Dir2Text
from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules

# Create exclusion rules
rules = GitIgnoreExclusionRules()
rules.load_rules(".gitignore")

# Process everything immediately
analyzer = Dir2Text(
    "path/to/project", 
    exclusion_rules=rules,
    follow_symlinks=True  # Optionally follow symlinks
)

# Access complete content
print(analyzer.tree_string)
print(analyzer.content_string)
```

## Output Formats

### XML Format
```xml
<file path="relative/path/to/file.py" tokens="150">
def example():
    print("Hello, world!")
</file>
<symlink path="docs/api.md" target="../README.md" />
```

### JSON Format
```json
{
  "type": "file",
  "path": "relative/path/to/file.py",
  "content": "def example():\n    print(\"Hello, world!\")",
  "tokens": 150
}
{
  "type": "symlink",
  "path": "docs/api.md",
  "target": "../README.md"
}
```

## Development

### Setup Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/rlichtenwalter/dir2text.git
   cd dir2text
   ```

2. Install development dependencies:
   ```bash
   poetry install --with dev
   ```

3. Install pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

### Running Tests

```bash
# Run specific quality control categories
poetry run tox -e format    # Run formatters
poetry run tox -e lint      # Run linters
poetry run tox -e test      # Run tests
poetry run tox -e coverage  # Run test coverage analysis
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the test suite
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses [anytree](https://github.com/c0fec0de/anytree) for tree data structures
- .gitignore pattern matching uses [pathspec](https://github.com/cpburnz/python-pathspec)
- Token counting functionality is provided by OpenAI's [tiktoken](https://github.com/openai/tiktoken)

## Requirements

- Python 3.9+
- Poetry (recommended) or pip
- Optional: Rust compiler and Cargo (for token counting feature)

## Project Status

This project is actively maintained. Issues and pull requests are welcome.

## FAQ

**Q: Why use streaming processing?**  
A: Streaming allows processing of large directories and files with constant memory usage, making it suitable for processing repositories of any size.

**Q: How does dir2text handle symbolic links?**  
A: By default, dir2text represents symlinks as symbolic links in both tree and content output without following them. With the `-L` option, it follows symlinks similar to Unix tools like `find -L`. In both modes, symlink loop detection prevents infinite recursion.

**Q: Can I use this with binary files?**  
A: The tool is designed for text files. Binary files should be excluded using the exclusion rules feature.

**Q: What models are supported for token counting?**  
A: The token counting feature uses OpenAI's tiktoken library with the following primary models and encodings:
- cl100k_base encoding:
  - GPT-4 models (gpt-4, gpt-4-32k)
  - GPT-3.5-Turbo models (gpt-3.5-turbo)
- p50k_base encoding:
  - Text Davinci models (text-davinci-003)

For other language models, using a similar model's tokenizer (like gpt-4) can provide useful approximations of token counts. While the counts may not exactly match your target model's tokenization, they can give a good general estimate. The default model is "gpt-4", which uses cl100k_base encoding and provides a good general-purpose tokenization.

**Q: What happens if I specify a model that doesn't have a dedicated tokenizer?**  
A: The library will suggest using a well-supported model like 'gpt-4' or 'text-davinci-003' for token counting. While token counts may not exactly match your target model, they can provide useful approximations for most modern language models.

**Q: How can I control where statistics are displayed?**  
A: Use the `-s/--stats` option to control where statistics are displayed:
  - `-s` or `-s stderr`: Print statistics to stderr (default)
  - `-s stdout`: Print statistics to stdout
  - `-s file`: Include statistics in the output file (requires `-o`)

**Q: Is token counting required for statistics reporting?**  
A: No. Basic statistics (file count, directory count, etc.) are available without token counting. Including token counts in statistics requires the `-c/--count` option to be specified in addition to `-s/--stats`.

## Contact

Ryan N. Lichtenwalter - rlichtenwalter@gmail.com

Project Link: [https://github.com/rlichtenwalter/dir2text](https://github.com/rlichtenwalter/dir2text)