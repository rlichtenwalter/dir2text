# Installation Guide

This guide covers installation methods for dir2text and its optional token counting feature.

## Prerequisites

- Python 3.9.1 or later
- pip or Poetry for package management
- Optional: Rust compiler and Cargo (for token counting feature)

## Basic Installation

### Using pip

```bash
# Basic installation
pip install dir2text

# With token counting support
pip install "dir2text[token_counting]"
```

### Using Poetry

```bash
# Basic installation
poetry add dir2text

# With token counting support
poetry add "dir2text[token_counting]"
```

## Token Counting Support

The token counting feature requires additional dependencies:
- tiktoken library
- Rust compiler (for tiktoken installation)

### Installing Rust (for token counting)

#### Linux/macOS:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

#### Windows:
1. Download and run [rustup-init.exe](https://win.rustup.rs/)
2. Follow the installation prompts

Ensure Rust is in your PATH before installing dir2text with token counting.

## Virtual Environments

Using virtual environments is recommended:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix-like systems:
source venv/bin/activate

# Install dir2text
pip install dir2text
```

## Verifying Installation

After installation, verify everything works:

```bash
# Check CLI availability
dir2text --help

# Check Python package import
python -c "import dir2text; print(dir2text.__version__)"

# Test token counting if installed
python -c """
from dir2text.token_counter import TokenCounter
try:
    counter = TokenCounter()
    print('Token counting available')
except ImportError:
    print('Token counting not available')
"""
```

## Common Issues and Solutions

### Token Counter Not Available

If you see "TokenizerNotAvailableError":
1. Install with token counting support:
   ```bash
   pip install "dir2text[token_counting]"
   ```
2. Ensure Rust compiler is installed
3. Verify Python version is 3.9.1 or later

### Permission Errors

If you encounter permission errors:
1. On Unix-like systems:
   - Use `sudo` or install in a virtual environment
2. On Windows:
   - Run command prompt as administrator
   - Use a virtual environment

### Poetry Installation Issues

If Poetry installation fails:
1. Update Poetry:
   ```bash
   poetry self update
   ```
2. Clear Poetry's cache:
   ```bash
   poetry cache clear . --all
   ```
3. Try creating a new virtual environment:
   ```bash
   poetry env remove --all
   poetry install
   ```

## Platform-Specific Notes

### Unix-like Systems

- Ensure write permissions for installation directory
- Consider using user-level installation: `pip install --user`
- Use virtual environments for isolation

### Windows

- Run installers with administrator privileges if needed
- Use Windows PowerShell for best compatibility
- Ensure Python is in system PATH

## Upgrading

```bash
# Using pip
pip install --upgrade dir2text

# Using Poetry
poetry update dir2text
```

## Uninstallation

```bash
# Using pip
pip uninstall dir2text

# Using Poetry
poetry remove dir2text
```

## Getting Help

If you encounter installation issues:
1. Check the error message carefully
2. Verify prerequisites are met
3. Try the solutions in Common Issues
4. Create an issue in the [GitHub repository](https://github.com/rlichtenwalter/dir2text)