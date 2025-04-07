# Change Log

All notable changes to this project will be documented in this file.

This project adheres at least loosely to Semantic Versioning.

## Version 1.1.0 (2025-04-07)
This release focuses on usability enhancements, particularly in exclusion rule support and output control.

### Added
- Format specification in the CLI with '-f' in addition to the previously existing '--format'.
- Ability to direct final counting report to stderr instead of stdout in the CLI with '--report-to-stderr'.
- Specification of multiple exclusion rules both in the API and in the CLI (with multiple specifications of the '-e, --exclude' option).
- Specification of an individual files to ignore in the API and in the CLI (with the '-i, --ignore') option, which can be provided multiple times.

### Changed
- Interfaces standardized on os.PathLike with os.Path in implementations instead of a mixture of str and os.Path.

### Fixed
- Nothing.

## Version 1.0.1 (2024-10-24)
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

