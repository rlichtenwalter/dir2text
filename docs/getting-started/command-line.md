# Command Line Interface

## Overview

The `dir2text` command-line interface converts directory structures into text representations suitable for analysis or LLM processing.

## Basic Usage

```bash
dir2text [OPTIONS] DIRECTORY
```

## Options

| Option | Description | Example |
|--------|-------------|---------|
| `-V, --version` | Show version information and exit | `dir2text --version` |
| `-o, --output FILE` | Output file path | `dir2text dir -o output.txt` |
| `-e, --exclude FILE` | Path to exclusion file (can be specified multiple times) | `dir2text dir -e .gitignore -e .npmignore` |
| `-i, --ignore PATTERN` | Individual pattern to exclude (can be specified multiple times) | `dir2text dir -i "*.pyc" -i "node_modules/"` |
| `-f, --format FORMAT` | Output format (xml/json) | `dir2text dir -f json` |
| `-L, --follow-symlinks` | Follow symbolic links during traversal | `dir2text dir -L` |
| `-T, --no-tree` | Skip directory tree | `dir2text dir -T` |
| `-C, --no-contents` | Skip file contents | `dir2text dir -C` |
| `-c, --count` | Enable token counting and embed token counts in file metadata output | `dir2text dir -c` |
| `-s, --stats` | Print statistics report (stderr, stdout, or file) | `dir2text dir -s` |
| `-t, --tokenizer MODEL` | Model for token counting | `dir2text dir -c -t gpt-4` |
| `-P, --permission-action ACTION` | Permission error handling | `dir2text dir -P warn` |

## Version Information

```bash
dir2text --version

# Example output:
dir2text X.X.X
```

When the version flag is used, the program prints the version and exits immediately, ignoring any other flags.

## Output Formats

### XML Format (Default)
```bash
dir2text /path/to/project

# Example output:
<file path="src/main.py">
def main():
    print("Hello, World!")
</file>
<symlink path="link/to/readme.md" target="../README.md" />
```

### JSON Format
```bash
dir2text /path/to/project -f json

# Example output:
{"type": "file", "path": "src/main.py", "content": "def main():\n    print(\"Hello, World!\")\n"}
{"type": "symlink", "path": "link/to/readme.md", "target": "../README.md"}
```

## Directory Structure

```bash
# Show only directory structure
dir2text /path/to/project --no-contents

# Example output:
project/
├── src/
│   ├── main.py
│   └── utils/
│       └── helpers.py
├── link_to_src → ./src/ [symlink]
└── README.md
```

## Symbolic Link Handling

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

## File Selection

### Using Exclusion Files
```bash
# Use single exclusion file
dir2text /path/to/project -e .gitignore

# Combine multiple exclusion files
dir2text /path/to/project -e .gitignore -e .npmignore -e custom.ignore
```

When using multiple exclusion files, they are processed in the order specified on the command line. This is important when using negation patterns (starting with `!`), as later rules can override earlier ones.

Common exclusion patterns:
```gitignore
# Python artifacts
__pycache__/
*.pyc

# Build directories
build/
dist/
```

### Using Direct Patterns

```bash
# Exclude patterns directly
dir2text /path/to/project -i "*.pyc" -i "node_modules/"

# Mix file-based and direct pattern exclusions
dir2text /path/to/project -e .gitignore -i "*.log" -i "!important.log"
```

## Permission Handling

Control how permission errors are handled:

```bash
# Ignore permission errors (default)
dir2text /path/to/project -P ignore

# Show warnings but continue
dir2text /path/to/project -P warn

# Stop on permission errors
dir2text /path/to/project -P fail
```

## Token Counting

Token counting requires the token_counting extra:

```bash
# Install with token counting
pip install "dir2text[token_counting]"

# Enable token counting (embeds counts in output)
dir2text -c /path/to/project

# Use specific model for counting
dir2text -c -t gpt-4 /path/to/project

# Example output:
<file path="src/main.py" tokens="42">
def main():
    print("Hello, World!")
</file>
```

Supported models:
- `gpt-4` (default)
- `gpt-3.5-turbo`
- `text-davinci-003`

## Statistics Reporting

Control whether and where statistics are displayed:

```bash
# Print statistics to stderr (default)
dir2text -s stderr /path/to/project

# Print statistics to stdout
dir2text -s stdout /path/to/project

# Include statistics in the output file
dir2text -s file -o output.txt /path/to/project

# Show token counts in statistics (combined with -c)
dir2text -s stderr -c /path/to/project
```

Statistics include counts of directories, files, symlinks, lines, and characters. Token counts are only included when `-c` is also specified.

## Common Use Cases

### Project Documentation
```bash
# Generate directory structure only
dir2text /path/to/project --no-contents > structure.txt

# Full documentation in JSON
dir2text /path/to/project \
    -f json \
    -o documentation.json
```

### LLM Analysis
```bash
# Prepare for LLM with token counting
dir2text \
    -e .gitignore \
    -c \
    -o project_for_llm.txt \
    /path/to/project

# Include statistics in a separate file
dir2text \
    -e .gitignore \
    -c \
    -s stderr \
    /path/to/project \
    > project_for_llm.txt 2> stats.txt
```

### Including External Content via Symlinks
```bash
# Follow symbolic links to include external content
dir2text -L /path/to/project -o project_with_linked_content.txt
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime error |
| 2 | Command-line syntax error |
| 126 | Permission denied |
| 130 | Interrupted by SIGINT (Ctrl+C) |
| 141 | Broken pipe (SIGPIPE) on Unix-like systems |

## Error Handling

### Permission Errors
```bash
# Use appropriate permission action
dir2text /path/to/project -P warn
```