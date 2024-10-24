# Change Log

All notable changes to this project will be documented in this file.

This project adheres at least loosely to Semantic Versioning.

## Version 1.0.0 (2024-10-24)
This is the initial public release of dir2text. It is largely tested and stable but should still be regarded as beta.

### New Features
- Extensible exclusion rule system with .gitignore style exclusions supported out of the box.
- Extensible output format system with XML and JSON supported out of the box.
- Central streaming philosophy for large file support without high memory consumption.
- Carefully designed API that supports efficient implementation of future new features.
- Feature-rich CLI that exposes the bulk of the API functionality.

### Bug Fixes
- None (initial public release).

### Known Issues
- Symbolic link loop protection is not implemented. Application on structures with loops will hang.
- Unit test design and converage is fair but not great. Better design and coverage are desirable.
- Documentation is also fair but not great.

