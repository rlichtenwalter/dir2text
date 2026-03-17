# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

No changes yet.

## [3.1.0] - 2026-03-16

### Changed
- Migrate from Poetry and tox to uv for dependency management, builds, and task orchestration
- Update pre-commit hooks to use direct `uv run` commands instead of tox environments
- Update CI pipeline to use uv instead of Poetry
- Replace Poetry references in error messages and documentation with pip/uv equivalents

### Removed
- Remove unused `detection_error` field from `FileInfo` dataclass
- Remove tox dependency and configuration

### Fixed
- Fix binary action "warn" mode terminating after first binary file instead of continuing
- Replace magic sentinel `FileIdentifier(-1, -1)` with `Optional[FileIdentifier]` to eliminate ambiguity in symlink loop detection
- Correct misleading code comments about metrics counting delegation and binary detection error handling
- Add missing `None` assertions in tests for `Optional` return types from `get_tree()` and `token_count`
- Fix integration tests with incorrect assertions for binary action, max file size, JSON format, and gitignore negation

## [3.0.2] - 2026-03-07

### Changed
- Replace black, isort, flake8, and mypy with ruff (linting + formatting) and pyright (strict type checking)
- Update tox environments and pre-commit hooks for new tooling
- Modernize type annotations to use builtin generics and `NamedTuple`
- Add abstract `has_rules()` method to `BaseExclusionRules` requiring subclass implementation
- Add `has_rules()` implementation to `GitIgnoreExclusionRules` based on pattern count
- Use `os.stat()` instead of `Path.stat(follow_symlinks=)` for Python 3.9 compatibility
- Reorder text encoding list in binary detection to try discriminating encodings before latin-1

### Fixed
- Fix `signal.SIGPIPE` crash on Windows by guarding all SIGPIPE references behind platform check
- Fix latent closure bug in symlink iterator where loop variable was captured by reference
- Add proper exception chaining (`from e`/`from None`) to all re-raises
- Remove dead code in `_create_node` child filter that could never remove a node
- Fix token double-counting when output strategy requires tokens in start tag (XML)
- Fix `SafeWriter._closed` not being set when `close()` raises a non-EPIPE error
- Fix `directory_count` returning -1 when tree is `None`
- Replace fragile `rstrip("}")` with precise `rfind("}")` slice in JSON strategy
- Simplify root node name logic that had three identical branches
- Fix size exclusion rules resolving relative paths against CWD instead of the scanned directory
- Fix `[project.urls]` in pyproject.toml to use `[tool.poetry.urls]` for Poetry compatibility

## [3.0.1] - 2025-08-07

### Fixed
- Change tiktoken dependency specification from `^0.6.0` to `>=0.6.0`

## [3.0.0] - 2025-08-06

### Added
- Add support for maximum file size specification via `-M, --max-file-size`
- Add size exclusion rules class to support maximum file size
- Add composite exclusion rules class to support composable exclusion rules
- Add support for binary files with base64 encoding
- Add `-B, --binary-action` CLI option accepting 'ignore', 'warn', 'encode', or 'fail'
- Implement binary file detection heuristic

### Changed
- **BREAKING**: Output strategies now include content type information ("text" or "binary")
- **BREAKING**: Several API methods have new arguments related to binary file handling preceding preexisting arguments
- Change `token_counting` extra minimum tiktoken version from 0.8.0 to 0.6.0

### Fixed
- Fix exclusion rules with trailing slash excluding underlying files but still showing the matching directory in tree display

## [2.0.0] - 2025-04-11

### Added
- Add support for format specification using `-f` as a short form of `--format`
- Add support for specifying multiple exclusion rules both via files (-e/--exclude) and direct patterns (-i/--ignore)
- Implement context manager support in SafeWriter
- Improve signal handling during SafeWriter close operations

### Changed
- **BREAKING**: Remove direct `exclude_files` support in StreamingDir2Text and Dir2Text; now requires a subclass of `BaseExclusionRules`
- **BREAKING**: Remove `-c, --counts` flag; statistics reporting now controlled through `-s, --summary=DEST`
- Change default CLI behavior to no longer print summary reports by default
- Modify token counting so `-t, --tokenizer MODEL` implicitly enables counting
- Enhance symlink handling with improved loop detection and exclusion rule interaction
- Refactor CLI code to use SafeWriter as a context manager
- Standardize interfaces on `os.PathLike` with `Path` in implementations

### Fixed
- Fix bug in SafeWriter allowing file objects to be prematurely garbage collected

## [1.0.1] - 2024-10-24

### Added
- Add project description in pyproject.toml

## [1.0.0] - 2024-10-24

### Added
- Extensible exclusion rule system with .gitignore style exclusions
- Extensible output format system with XML and JSON support
- Streaming architecture for large file support without high memory consumption
- Feature-rich CLI exposing the bulk of API functionality
