# Change Log

All notable changes to this project will be documented in this file.

This project adheres at least loosely to Semantic Versioning.

## Version 2.0.0 (2025-04-11)
This major version release focuses on usability enhancements, particularly in exclusion rule support, symbolic link handling, and output control.

### Added
- Added support for format specification using `-f` as a short form of `--format`.
- Added support for specifying multiple exclusion rules both via files (-e/--exclude) and direct patterns (-i/--ignore), preserving the exact ordering for proper pattern precedence.
- Implemented context manager support in SafeWriter, enabling usage with `with` statements.
- Improved signal handling during SafeWriter close operations.

### Changed
- **BREAKING**: Removed direct `exclude_files` support in StreamingDir2Text and Dir2Text, which now require a subclass of dir2text.exclusion_rules.BaseExclusionRules instead.
- **BREAKING**: Removed the `-c, --counts` flag. Statistics reporting is now controlled exclusively through the new `-s, --summary=DEST` option, which requires a destination argument that can be 'stderr', 'stdout', or 'file' (with '-o').
- Changed default CLI behavior to no longer print summary reports by default.
- Modified token counting behavior so that specifying the `-t, --tokenizer MODEL` option implicitly enables token counting without requiring an additional flag.
- Enhanced symlink handling with improved loop detection and proper interaction with exclusion rules.
- Refactored CLI code to use SafeWriter as a context manager.
- Improved error handling for signal interruption during SafeWriter resource cleanup.
- Standardized interfaces on os.PathLike with os.Path in implementations instead of a mixture of str and os.Path.
- Refactored CLI code to break out parsing, output writing, and signal handling functions separate from orchestration.

### Fixed
- Fixed a bug in SafeWriter CLI-internal class that allowed file objects to be prematurely garbage collected.

### Migration Guide
If you previously used:
```python
analyzer = StreamingDir2Text(directory, exclude_files=[".gitignore"])
```

You should now use:
```python
rules = GitIgnoreExclusionRules()
rules.load_rules(".gitignore")
analyzer = StreamingDir2Text(directory, exclusion_rules=rules)
```

### Known Issues
- None.

## Version 1.0.1 (2024-10-24)
Added a project description for better presentation on PyPI.

### Added
- Project description in pyproject.toml.

### Changed
- Nothing.

### Fixed
- Nothing.

### Known Issues
- Symbolic link loop protection is not implemented. Application on structures with loops will hang.
- Unit test design and converage is fair but not great. Better design and coverage are desirable.
- Documentation is also fair but not great.

## Version 1.0.0 (2024-10-24)
This is the initial public release of dir2text. It is largely tested and stable but should still be regarded as beta.

### Added
- Extensible exclusion rule system with .gitignore style exclusions supported out of the box.
- Extensible output format system with XML and JSON supported out of the box.
- Central streaming philosophy for large file support without high memory consumption.
- Carefully designed API that supports efficient implementation of future new features.
- Feature-rich CLI that exposes the bulk of the API functionality.

### Changed
- Nothing (initial public release).

### Fixed
- Nothing (initial public release).

### Known Issues
- Symbolic link loop protection is not implemented. Application on structures with loops will hang.
- Unit test design and converage is fair but not great. Better design and coverage are desirable.
- Documentation is also fair but not great.

