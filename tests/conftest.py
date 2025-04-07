"""Test configuration and fixtures for dir2text."""


def pytest_addoption(parser):
    """Add custom command-line options for tests."""
    parser.addoption("--run-cli-tests", action="store_true", default=False, help="Run CLI integration tests (slow)")
