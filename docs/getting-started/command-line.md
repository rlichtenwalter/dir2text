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
| `-L, --follow-symlinks` | Follow symbolic links during traversal | `dir2text dir -L` |
| `-f, --format FORMAT` | Output format (xml/json) | `dir2text dir -f json` |
| `-T, --no-tree` | Skip directory tree | `dir2text dir -T` |
| `-C, --no-contents` | Skip file contents | `dir2text dir -C` |
| `-s, --summary` | Print summary report (stderr, stdout, or file) | `dir2text dir -s stderr` |
| `-t, --tokenizer MODEL` | Model for token counting | `dir2text dir -t gpt-4` |
| `-P, --permission-action ACTION` | Permission error handling | `dir2text dir -P warn` |
| `-B, --binary-action ACTION` | Binary file handling | `dir2text dir -B encode` |
| `-M, --max-file-size SIZE` | Maximum file size to include | `dir2text dir -M 50MB` |

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
<file path="src/main.py" content_type="text">
def main():
    print("Hello, World!")
</file>
<symlink path="link/to/readme.md" target="../README.md" />
```

### JSON Format
```bash
dir2text /path/to/project -f json

# Example output:
{"type": "file", "path": "src/main.py", "content_type": "text", "content": "def main():\n    print(\"Hello, World!\")\n"}
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

When using multiple exclusion files, they are processed in the order specified on the command line. This is important when using negation patterns (starting with `!`), because later rules can override earlier ones.

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

### Limiting File Sizes

Control which files are included based on their size:

```bash
# Exclude files larger than 50MB
dir2text /path/to/project -M 50MB

# Use different units
dir2text /path/to/project -M 1GB        # 1 gigabyte
dir2text /path/to/project -M 1GiB       # 1 gibibyte (binary)
dir2text /path/to/project -M 2048       # 2048 bytes
dir2text /path/to/project -M "2.5 MB"   # 2.5 megabytes (with spaces)

# Combine size limits with other exclusions
dir2text /path/to/project -e .gitignore -M 100MB
```

Supported size formats:
- **Decimal units**: KB, MB, GB, TB, PB (powers of 1000)
- **Binary units**: KiB, MiB, GiB, TiB, PiB (powers of 1024)
- **Raw bytes**: Any integer number
- **Decimal values**: 1.5MB, 2.75GB, etc.
- **With spaces**: "1 GB", "500 MB"

Files exceeding the size limit are completely excluded from both the directory tree and file contents output. Directories are never excluded based on size limits.

For symbolic links, the size of the target file is checked (not the symlink itself), so large files remain excluded even when accessed through symlinks.
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

## Binary File Handling

Control how binary files are processed:

```bash
# Ignore binary files (default) - skip silently
dir2text /path/to/project -B ignore

# Show warnings for binary files but skip them
dir2text /path/to/project -B warn

# Include binary files as base64-encoded content
dir2text /path/to/project -B encode

# Stop processing when binary files are encountered
dir2text /path/to/project -B fail
```

### Binary File Detection

Files are automatically detected as binary using a two-phase approach for optimal performance:

1. **Fast extension-based detection**: Common extensions like `.jpg`, `.png`, `.mp4`, `.exe` are immediately classified as binary without reading file content
2. **Content analysis fallback**: Files with unknown extensions are analyzed by reading a small chunk to detect:
   - Null bytes (strong binary indicator)
   - Text encoding compatibility (UTF-8, Latin-1, CP1252, UTF-16)
   - Control character ratios

### Binary File Actions

**ignore (default)**
```bash
dir2text /path/to/project -B ignore

# Output: Binary files are silently skipped
<directory path="project">
  <file path="README.md">...</file>
  <!-- image.jpg skipped -->
</directory>
```

**warn**
```bash
dir2text /path/to/project -B warn

# Output: Warnings printed to stderr, files still skipped
Warning: Skipping binary file: images/photo.jpg
<directory path="project">
  <file path="README.md">...</file>
  <!-- photo.jpg skipped with warning -->
</directory>
```

**encode** 
```bash
dir2text /path/to/project -B encode

# Output: Binary content included as base64
<file path="images/logo.png [binary]" content_type="binary">
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
AAALEgAACxIB0t1+/AAAABZ0RVh0Q3JlYXRpb24gVGltZQAwMS8yOS8xMC7F9wAABaJJREFUOMtV
...
</file>
```

**fail**
```bash
dir2text /path/to/project -B fail

# Output: Processing stops at first binary file
Error: Binary file encountered: images/photo.jpg
Use --binary-action to specify how binary files should be handled.
```

### Performance Considerations

The binary detection system is optimized for performance:

- **Extension-based fast-path**: Files with known extensions (`.py`, `.js`, `.jpg`, `.mp4`) are classified instantly without file I/O
- **Streaming base64 encoding**: When using `-B encode`, binary files are processed in optimized chunks to maintain constant memory usage
- **Token counting consistency**: Base64-encoded binary files support token counting with the same streaming approach as text files

## Token Counting

Token counting requires the token_counting extra:

```bash
# Install with token counting
pip install "dir2text[token_counting]"

# Enable token counting by specifying tokenizer model
dir2text -t gpt-4 /path/to/project

# Example output with token counts:
<file path="src/main.py" content_type="text" tokens="42">
def main():
    print("Hello, World!")
</file>
```

Supported models:
- `gpt-4` (recommended default)
- `gpt-3.5-turbo`
- `text-davinci-003`

## Summary Reporting

The summary always includes directory, file, symlink, line, and character counts. Token counts are only included when a tokenizer model is specified with `-t`.

Control where summary information is displayed:

```bash
# Print summary to stderr
dir2text -s stderr /path/to/project

# Print summary to stdout
dir2text -s stdout /path/to/project

# Include summary in the output file
dir2text -s file -o output.txt /path/to/project

# Include token counts in summary by specifying tokenizer
dir2text -s stderr -t gpt-4 /path/to/project
```

Example summary output:
```
Directories: 5
Files: 12
Symlinks: 2
Lines: 245
Tokens: 1503  # Only shown when -t is specified
Characters: 12450
```

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
# Prepare for LLM with token counting and size limits (skip binary files)
dir2text \
    -e .gitignore \
    -M 1MB \
    -B ignore \
    -t gpt-4 \
    -o project_for_llm.txt \
    /path/to/project

# Include binary files as base64 for multimodal LLM analysis
dir2text \
    -e .gitignore \
    -M 1MB \
    -B encode \
    -t gpt-4 \
    -o project_with_media.txt \
    /path/to/project

# Show binary file warnings to track what's being skipped
dir2text \
    -e .gitignore \
    -M 500KB \
    -B warn \
    -t gpt-4 \
    -s stderr \
    /path/to/project \
    > project_for_llm.txt 2> stats_and_warnings.txt

# Focus on code files only with reasonable size limits
dir2text \
    -e .gitignore \
    -i "*.md" -i "*.txt" -i "*.json" \
    -M 100KB \
    -B ignore \
    -t gpt-4 \
    /path/to/project
```

### Binary File Processing
```bash
# Skip binary files silently (fastest, most common)
dir2text /path/to/project -B ignore

# Get visibility into binary files without including content
dir2text /path/to/project -B warn 2> binary_files_found.log

# Include images and other binary assets for multimodal processing
dir2text /path/to/project -B encode -o project_with_assets.txt

# Ensure no binary files are present in output (strict text-only)
dir2text /path/to/project -B fail
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

### Binary File Errors
```bash
# Handle binary files based on your needs
dir2text /path/to/project -B warn    # Show warnings but continue
dir2text /path/to/project -B fail    # Stop at first binary file
dir2text /path/to/project -B encode  # Include as base64
```

### Token Counting Errors
If token counting is requested but tiktoken is not available, a helpful error message is displayed:
```
Error: Token counting was requested with -t/--tokenizer, but the required tiktoken library is not installed.
To enable token counting, install dir2text with the 'token_counting' extra:
    pip install "dir2text[token_counting]"
    # or with Poetry:
    poetry add "dir2text[token_counting]"
```