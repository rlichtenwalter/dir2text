# dir2text

A Python library and command-line tool for expressing directory structures and file contents in formats suitable for Large Language Models (LLMs). It combines directory tree visualization with file contents in a memory-efficient, streaming format.

## Features

- Tree-style directory structure visualization
- Complete file contents with proper escaping
- Memory-efficient streaming processing
- Multiple output formats (XML, JSON)
- Easy extensibility for new formats
- Support for exclusion patterns (e.g., .gitignore rules)
- Optional token counting for LLM context management
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

# Exclude files matching .gitignore patterns
dir2text -e .gitignore /path/to/project

# Count tokens for LLM context management
dir2text -c /path/to/project

# Generate JSON output and save to file
dir2text --format json -o output.json /path/to/project

# Skip tree or content sections
dir2text -T /path/to/project     # Skip tree visualization
dir2text -C /path/to/project     # Skip file contents
```

### Python API

Basic usage:
```python
from dir2text import StreamingDir2Text

# Initialize the analyzer
analyzer = StreamingDir2Text("path/to/project")

# Stream the directory tree
for line in analyzer.stream_tree():
    print(line, end='')

# Stream file contents
for chunk in analyzer.stream_contents():
    print(chunk, end='')

# Get metrics
print(f"Processed {analyzer.file_count} files in {analyzer.directory_count} directories")
```

Memory-efficient processing with exclusions and token counting:
```python
from dir2text import StreamingDir2Text

# Initialize with options
analyzer = StreamingDir2Text(
    directory="path/to/project",
    exclude_file=".gitignore",
    output_format="json",
    tokenizer_model="gpt-4"
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
print(f"Lines: {analyzer.line_count}")
print(f"Tokens: {analyzer.token_count}")
print(f"Characters: {analyzer.character_count}")
```

Immediate processing (for smaller directories):
```python
from dir2text import Dir2Text

# Process everything immediately
analyzer = Dir2Text("path/to/project")

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
```

### JSON Format
```json
{
  "path": "relative/path/to/file.py",
  "content": "def example():\n    print(\"Hello, world!\")",
  "tokens": 150
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
A: dir2text follows symbolic links to both files and directories. While this enables complete directory traversal, no symlink loop detection is currently implemented. Users should be cautious when processing directories with circular symlinks, as this could lead to infinite recursion. Future versions may add configuration options for symlink handling and loop prevention.

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

## Contact

Ryan N. Lichtenwalter - rlichtenwalter@gmail.com

Project Link: [https://github.com/rlichtenwalter/dir2text](https://github.com/rlichtenwalter/dir2text)
