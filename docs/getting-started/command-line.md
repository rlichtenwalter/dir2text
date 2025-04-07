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
| `-o, --output FILE` | Output file path | `dir2text dir -o output.txt` |
| `-e, --exclude FILE` | Path to exclusion file (can be specified multiple times) | `dir2text dir -e .gitignore -e .npmignore` |
| `-f FORMAT` | Output format (xml/json) | `dir2text dir -f json` |
| `-T, --no-tree` | Skip directory tree | `dir2text dir -T` |
| `-C, --no-contents` | Skip file contents | `dir2text dir -C` |
| `-t, --tokenizer MODEL` | Model for token counting | `dir2text dir -t gpt-4` |
| `-P, --permission-action ACTION` | Permission error handling | `dir2text dir -P warn` |

## Output Formats

### XML Format (Default)
```bash
dir2text /path/to/project

# Example output:
<file path="src/main.py">
def main():
    print("Hello, World!")
</file>
```

### JSON Format
```bash
dir2text /path/to/project -f json

# Example output:
{
  "path": "src/main.py",
  "content": "def main():\n    print(\"Hello, World!\")\n"
}
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
└── README.md
```

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

# Use specific model for counting
dir2text /path/to/project -t gpt-4

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
dir2text /path/to/project \
    -e .gitignore \
    -t gpt-4 \
    -o project_for_llm.txt
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime error |
| 2 | Command-line syntax error |
| 126 | Permission denied |
| 130 | Interrupted by SIGINT (Ctrl+C) |

## Error Handling

### Permission Errors
```bash
# Use appropriate permission action
dir2text /path/to/project -P warn
```