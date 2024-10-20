# dir2text

A library and script for expressing a directory in terms of a file system tree and complete file text. Allows for various exclusion patterns. Essentially operates like a limited version of tar but with a different set of output format conventions.

Useful for things like submitting a repository to an LLM for interactive work.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management. We recommend using Poetry for the best development experience, but we also provide instructions for traditional pip installation.

### Using Poetry (Recommended)

1. First, [install Poetry](https://python-poetry.org/docs/#installation) if you haven't already.
2. Clone the repository:
   ```
   git clone https://github.com/yourusername/dir2text.git
   cd dir2text
   ```
3. Install the project and its dependencies:
   ```
   poetry install
   ```
4. Activate the virtual environment:
   ```
   poetry shell
   ```

#### Optional Extras

- To install with token counting functionality:
  ```
  poetry install --extras token_counting
  ```
- To install all optional dependencies:
  ```
  poetry install --extras all
  ```

### Using pip

If you prefer not to use Poetry, you can install the project using pip:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/dir2text.git
   cd dir2text
   ```
2. (Optional) Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install the project and its dependencies:
   ```
   pip install .
   ```

#### Optional Extras

- To install with token counting functionality:
  ```
  pip install .[token_counting]
  ```
- To install all optional dependencies:
  ```
  pip install .[all]
  ```

### Token Counting Functionality

The `token_counting` extra enables an option to count tokens in the input. This feature requires the installation of additional dependencies, which may significantly increase the total package size.

**Note:** The `tiktoken` package, used for token counting, requires a Rust compiler (e.g., `rustc`) and Cargo to be available and included in your system's PATH during installation.

## Development

For development, you'll need to install the development dependencies as well:

### With Poetry:
```
poetry install --with dev
```

### With pip:
```
pip install -e ".[dev]"
```

## Running Tests

After installation, you can run tests using:

### With Poetry:
```
poetry run test
```

### With pip:
```
pytest
```

For more commands (linting, type checking, etc.), refer to the "Scripts" section below.

## Scripts

The project includes several scripts for common tasks:

- Run tests: `poetry run test`
- Lint code: `poetry run lint`
- Type check: `poetry run typecheck`
- Format code: `poetry run format`
- Run test coverage: `poetry run coverage`

If you're not using Poetry, you can run these commands directly (e.g., `pytest`, `flake8 src tests`, etc.).

## Usage

[Your usage instructions here]

## Contributing

Contributions are always welcome!

## License

This project is licensed under the MIT License - see the LICENSE file for details.