# Change Log

All notable changes to this project will be documented in this file.

This project adheres at least loosely to Semantic Versioning.

## Version 1.1.0 (2025-04-07)
This release focuses on usability enhancements, particularly in exclusion rule support and output control.

### Added
- Format specification in the CLI with '-f' in addition to the previously existing '--format'.
- Specification of multiple exclusion rules both in the API and in the CLI (with multiple specifications of the '-e, --exclude' option).
- Specification of an individual files to ignore in the API and in the CLI (with the '-i, --ignore') option, which can be provided multiple times.
- 

### Changed
- BREAKING CHANGE: StreamingDir2Text and Dir2Text now require passing a subclass of dir2text.exclusion_rules.BaseExclusionRules and no longer support a path list.
- Interfaces standardized on os.PathLike with os.Path in implementations instead of a mixture of str and os.Path.
- The statistics report is no longer printed by default with '-c, --counts'.
- The reporting of final statistics is now separately controlled with '-s, --stats=DEST', which takes a destination argument that can be 'stderr', 'stdout', or 'file' (with '-o').
- Refactored CLI code to break out parsing, output writing, and signal handling functions separate from orchestration.
- Converted SafeWriter CLI-internal class to a context manager.

### Fixed
- Addressed bug in SafeWriter CLI-internal class that allowed file objects to be prematurely garbage collected.

### Known Issues
- Symbolic link loop protection is not implemented. Application on structures with loops will hang.
- Unit test design and converage is fair but not great. Better design and coverage are desirable.
- Documentation is also fair but not great.

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

