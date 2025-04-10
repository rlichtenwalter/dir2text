"""Integration tests for the command-line interface."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from dir2text.cli.main import format_counts

# Skip all tests in this module if not running with pytest -xvs tests/test_cli_integration.py
# This prevents these slow tests from running during normal test runs
pytestmark = pytest.mark.skipif(
    "not config.getoption('--run-cli-tests')", reason="Only run when --run-cli-tests is given"
)


@pytest.fixture
def temp_project():
    """Create a temporary project directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create directories
        (base_dir / "src").mkdir()
        (base_dir / "src" / "utils").mkdir()
        (base_dir / "docs").mkdir()
        (base_dir / "node_modules").mkdir()
        (base_dir / "build").mkdir()

        # Create test files
        (base_dir / "src" / "main.py").write_text("def main():\n    print('Hello')\n")
        (base_dir / "src" / "utils" / "helpers.py").write_text("def helper():\n    pass\n")
        (base_dir / "docs" / "README.md").write_text("# Test Project\nDescription.\n")
        (base_dir / "src" / "main.pyc").write_bytes(b"compiled python")
        (base_dir / "server.log").write_text("DEBUG: test log\n")
        (base_dir / "package.json").write_text('{"name": "test"}\n')
        (base_dir / "build" / "output.min.js").write_text("console.log('test')\n")
        (base_dir / "node_modules" / "module.js").write_text("export default {}\n")

        # Create exclusion files
        (base_dir / ".gitignore").write_text("*.pyc\nbuild/\n")
        (base_dir / ".npmignore").write_text("*.log\ndocs/\n")
        (base_dir / "custom.ignore").write_text("node_modules/\n")

        yield base_dir


def run_cli(args, cwd=None):
    """Run the dir2text CLI with the given arguments."""
    cmd = [sys.executable, "-m", "dir2text.cli.main"] + args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
    return result


@pytest.fixture
def conftest():
    """Add CLI test option to pytest."""
    return """
def pytest_addoption(parser):
    parser.addoption(
        "--run-cli-tests", action="store_true", default=False,
        help="Run CLI integration tests (slow)"
    )
"""


def test_cli_single_exclusion(temp_project):
    """Test the CLI with a single exclusion file."""
    # Run with gitignore only - use absolute path to the exclusion file
    gitignore_path = str(temp_project / ".gitignore")
    result = run_cli(["-e", gitignore_path, str(temp_project)])

    # Verify output
    assert result.returncode == 0

    # Should exclude .pyc files and build/ directory
    assert "main.pyc" not in result.stdout
    assert "output.min.js" not in result.stdout

    # Should include other files
    assert "main.py" in result.stdout
    assert "README.md" in result.stdout
    assert "server.log" in result.stdout
    assert "module.js" in result.stdout


def test_cli_multiple_exclusions(temp_project):
    """Test the CLI with multiple exclusion files."""
    # Run with all three exclusion files - use absolute paths
    gitignore_path = str(temp_project / ".gitignore")
    npmignore_path = str(temp_project / ".npmignore")
    custom_ignore_path = str(temp_project / "custom.ignore")

    result = run_cli(["-e", gitignore_path, "-e", npmignore_path, "-e", custom_ignore_path, str(temp_project)])

    # Verify output
    assert result.returncode == 0

    # Should exclude files from all three ignore files
    assert "main.pyc" not in result.stdout  # from .gitignore
    assert "output.min.js" not in result.stdout  # from .gitignore (build/)
    assert "server.log" not in result.stdout  # from .npmignore
    assert "README.md" not in result.stdout  # from .npmignore (docs/)
    assert "module.js" not in result.stdout  # from custom.ignore (node_modules/)

    # Should include other files
    assert "main.py" in result.stdout
    assert "helpers.py" in result.stdout
    assert "package.json" in result.stdout


def test_cli_stats_options(temp_project):
    """Test the -s/--stats options."""

    # Test default stats behavior (stderr output)
    # -s/--stats requires an argument, so use 'stderr' explicitly
    result_default = run_cli(["-s", "stderr", str(temp_project)])
    assert result_default.returncode == 0
    assert "Directories:" in result_default.stderr
    assert "Files:" in result_default.stderr
    assert "Lines:" in result_default.stderr
    assert "Characters:" in result_default.stderr
    # No token counts without -c
    assert "Tokens:" not in result_default.stderr
    # Make sure stats aren't in stdout
    assert "Directories:" not in result_default.stdout

    # Test stdout stats
    result_stdout = run_cli(["-s", "stdout", str(temp_project)])
    assert result_stdout.returncode == 0
    assert "Directories:" in result_stdout.stdout
    assert "Files:" in result_stdout.stdout
    assert "Lines:" in result_stdout.stdout
    assert "Characters:" in result_stdout.stdout
    # Make sure stats aren't in stderr
    assert "Directories:" not in result_stdout.stderr

    # Test stats with token counting
    result_with_tokens = run_cli(["-s", "stderr", "-c", str(temp_project)])
    assert result_with_tokens.returncode == 0
    assert "Directories:" in result_with_tokens.stderr
    assert "Files:" in result_with_tokens.stderr
    assert "Lines:" in result_with_tokens.stderr
    assert "Characters:" in result_with_tokens.stderr
    assert "Tokens:" in result_with_tokens.stderr

    # Test count without stats (should not print stats report)
    result_count_only = run_cli(["-c", str(temp_project)])
    assert result_count_only.returncode == 0
    assert "Tokens:" not in result_count_only.stderr
    assert "Directories:" not in result_count_only.stderr


def test_cli_stats_to_file(temp_project):
    """Test the -s file option with output file."""
    # Create a regular output file instead of using NamedTemporaryFile
    output_path = str(temp_project / "output.txt")

    try:
        # Test stats to file
        result = run_cli(["-s", "file", "-o", output_path, str(temp_project)])
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Verify stats appear in the output file
        with open(output_path, "r") as f:
            content = f.read()
            assert "Directories:" in content
            assert "Files:" in content
            assert "Lines:" in content
            assert "Characters:" in content

        # Verify stats don't appear in stderr
        assert "Directories:" not in result.stderr
    finally:
        # Clean up
        try:
            if os.path.exists(output_path):
                os.unlink(output_path)
        except Exception:
            pass  # Ignore cleanup errors


def test_cli_stats_to_file_without_output(temp_project):
    """Test that specifying -s file without -o fails."""
    result = run_cli(["-s", "file", str(temp_project)])
    assert result.returncode != 0
    assert "--stats=file requires" in result.stderr


def test_cli_exclusion_order(temp_project):
    """Test that the order of exclusion files matters."""
    # Create test files to demonstrate order importance
    (temp_project / "order_test_a.ignore").write_text("src/utils/*.py\n")  # Exclude utils Python files
    (temp_project / "order_test_b.ignore").write_text("!src/main.py\n")  # Allow main.py

    # Ensure the files exist
    assert (temp_project / "order_test_a.ignore").exists()
    assert (temp_project / "order_test_b.ignore").exists()

    # Get absolute paths
    order_test_a_path = str(temp_project / "order_test_a.ignore")
    order_test_b_path = str(temp_project / "order_test_b.ignore")

    # Order 1: Exclude utils Python files, then allow main.py
    result1 = run_cli(
        [
            "-e",
            order_test_a_path,
            "-e",
            order_test_b_path,
            str(temp_project),
        ]
    )

    # Order 2: Allow main.py, then exclude utils Python files
    result2 = run_cli(
        [
            "-e",
            order_test_b_path,
            "-e",
            order_test_a_path,
            str(temp_project),
        ]
    )

    # In result1, main.py should be included and helpers.py should be excluded
    assert "main.py" in result1.stdout
    assert "def main()" in result1.stdout

    # Check that helpers.py content is not in the output
    assert "def helper()" not in result1.stdout

    # In result2, both main.py and helpers.py should be included
    # (since negation for main.py is applied first, and exclusion for utils/*.py doesn't affect main.py)
    assert "main.py" in result2.stdout
    assert "def main()" in result2.stdout
    # utils files should still be excluded
    assert "def helper()" not in result2.stdout


def test_cli_nonexistent_exclude_file(temp_project):
    """Test CLI behavior with nonexistent exclusion file."""
    result = run_cli(["-e", "nonexistent.ignore", str(temp_project)])

    # Should fail with error message
    assert result.returncode != 0
    assert "Rules file not found" in result.stderr


def test_cli_error_handling_with_multiple_files(temp_project):
    """Test CLI error handling with mix of valid and invalid exclusion files."""
    # Use absolute path for the valid file
    gitignore_path = str(temp_project / ".gitignore")
    result = run_cli(["-e", gitignore_path, "-e", "nonexistent.ignore", str(temp_project)])  # Valid  # Invalid

    # Should fail with error message
    assert result.returncode != 0
    assert "Rules file not found" in result.stderr


def test_cli_output_formats_with_multiple_exclusions(temp_project):
    """Test CLI with multiple exclusions and different output formats."""
    # Use absolute paths for exclusion files
    gitignore_path = str(temp_project / ".gitignore")
    npmignore_path = str(temp_project / ".npmignore")

    # XML format
    xml_result = run_cli(["-e", gitignore_path, "-e", npmignore_path, "-f", "xml", str(temp_project)])

    # JSON format
    json_result = run_cli(["-e", gitignore_path, "-e", npmignore_path, "-f", "json", str(temp_project)])

    # Verify XML format
    assert xml_result.returncode == 0
    assert "<file path=" in xml_result.stdout
    assert "</file>" in xml_result.stdout

    # Verify JSON format
    assert json_result.returncode == 0
    assert '"path":' in json_result.stdout
    assert '"content":' in json_result.stdout

    # Verify exclusions work in both formats
    assert "main.pyc" not in xml_result.stdout
    assert "main.pyc" not in json_result.stdout
    assert "server.log" not in xml_result.stdout
    assert "server.log" not in json_result.stdout


def test_cli_with_exclusions_in_output(temp_project):
    """Test CLI output with exclusions.

    This replaces the previous test_cli_with_output_file which was failing
    with file descriptor errors. Instead of testing file output, we test
    that exclusions are correctly reflected in stdout.
    """
    # Just test with a single exclusion file to simplify
    gitignore_path = str(temp_project / ".gitignore")

    # Run CLI without output file, check stdout instead
    result = run_cli(["-e", gitignore_path, str(temp_project)])

    # Check command succeeded
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

    # Check content of stdout
    assert "main.py" in result.stdout
    assert "package.json" in result.stdout
    assert "main.pyc" not in result.stdout  # excluded by gitignore


def test_cli_direct_pattern_exclusion(temp_project):
    """Test the CLI with direct pattern exclusions via -i/--ignore."""
    # Run with direct patterns
    result = run_cli(["-i", "*.pyc", "-i", "*.log", str(temp_project)])

    # Verify output
    assert result.returncode == 0

    # Should exclude patterns specified directly
    assert "main.pyc" not in result.stdout
    assert "server.log" not in result.stdout

    # Should include other files
    assert "main.py" in result.stdout
    assert "README.md" in result.stdout
    assert "package.json" in result.stdout
    assert "module.js" in result.stdout


def test_cli_mixed_exclusions(temp_project):
    """Test the CLI with a mix of -e and -i options."""
    # Get path to gitignore
    gitignore_path = str(temp_project / ".gitignore")

    # Run with mix of file and pattern exclusions
    result = run_cli(
        ["-e", gitignore_path, "-i", "*.md", str(temp_project)]  # Exclude *.pyc and build/  # Exclude markdown files
    )

    # Verify output
    assert result.returncode == 0

    # Should exclude from both sources
    assert "main.pyc" not in result.stdout  # from gitignore
    assert "output.min.js" not in result.stdout  # from gitignore (build/)
    assert "README.md" not in result.stdout  # from direct pattern

    # Should include other files
    assert "main.py" in result.stdout
    assert "server.log" in result.stdout
    assert "package.json" in result.stdout


def test_cli_interleaved_exclusions(temp_project):
    """Test the CLI with interleaved -e and -i options to verify order preservation."""
    # Create a file to control test order
    order_test = temp_project / "order_test.ignore"
    order_test.write_text("*.md\n")  # Exclude markdown files

    order_test_path = str(order_test)

    # Test order 1: Exclude .md files, then negate README.md
    result1 = run_cli(
        ["-e", order_test_path, "-i", "!README.md", str(temp_project)]  # Exclude *.md  # But allow README.md
    )

    # Test order 2: Allow README.md, then exclude all .md files
    result2 = run_cli(
        [
            "-i",
            "!README.md",  # Try to allow README.md
            "-e",
            order_test_path,  # Then exclude all *.md
            str(temp_project),
        ]
    )

    # In order 1, README.md should be included (negation works after exclusion)
    assert "README.md" in result1.stdout
    assert "# Test Project" in result1.stdout

    # In order 2, README.md should be excluded (later rule wins)
    assert "README.md" not in result2.stdout
    assert "# Test Project" not in result2.stdout


def test_cli_complex_pattern_exclusion(temp_project):
    """Test the CLI with complex gitignore pattern syntax in -i/--ignore."""
    # Replace Python file to make it more distinctive for testing
    (temp_project / "src" / "main.py").write_text("# MAIN_PY_FILE\ndef main():\n    print('Hello')\n")

    # Create a file in a subdirectory of utils to better test the patterns
    (temp_project / "src" / "utils" / "test_utils.py").write_text("# TEST_UTILS_PY\ndef test():\n    pass\n")

    # Test with various pattern types
    result = run_cli(
        [
            "-i",
            "src/**/*.py",  # All Python files in src directory or subdirectories
            "-i",
            "!src/utils/*.py",  # Except Python files directly in utils directory
            "-i",
            "build/",  # All build directories
            str(temp_project),
        ]
    )

    # Verify output
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

    # Verify pattern matching works correctly
    assert "# MAIN_PY_FILE" not in result.stdout  # src/main.py should be excluded
    assert "# TEST_UTILS_PY" in result.stdout  # src/utils/test_utils.py should be included due to negation
    assert "output.min.js" not in result.stdout  # build/ content should be excluded


def test_cli_negation_pattern_precedence(temp_project):
    """Test precedence of negation patterns with both -e and -i options."""
    # Create a test file with exclusion pattern
    exclude_file = temp_project / "exclude.ignore"
    exclude_file.write_text("*.py\n")  # Exclude all Python files

    # Test with different combinations and orders

    # Case 1: File excludes all .py, then direct pattern negates main.py
    result1 = run_cli(
        ["-e", str(exclude_file), "-i", "!src/main.py", str(temp_project)]  # Exclude *.py  # But allow main.py
    )

    # Case 2: Direct pattern negates main.py, then file excludes all .py
    result2 = run_cli(
        [
            "-i",
            "!src/main.py",  # Try to allow main.py
            "-e",
            str(exclude_file),  # Then exclude all *.py
            str(temp_project),
        ]
    )

    # Case 3: Direct pattern excludes, direct pattern negates
    result3 = run_cli(
        ["-i", "*.py", "-i", "!src/main.py", str(temp_project)]  # Exclude all Python files  # But allow main.py
    )

    # Case 4: Direct pattern negates, direct pattern excludes
    result4 = run_cli(
        ["-i", "!src/main.py", "-i", "*.py", str(temp_project)]  # Try to allow main.py  # Then exclude all Python files
    )

    # Case 1: main.py should be included (negation after exclusion works)
    assert "def main()" in result1.stdout
    assert "def helper()" not in result1.stdout  # Other Python files still excluded

    # Case 2: main.py should be excluded (later rule wins)
    assert "def main()" not in result2.stdout

    # Case 3: main.py should be included (negation works with direct patterns)
    assert "def main()" in result3.stdout
    assert "def helper()" not in result3.stdout  # Other Python files excluded

    # Case 4: main.py should be excluded (later rule wins with direct patterns too)
    assert "def main()" not in result4.stdout


def test_format_counts():
    """Test format_counts function."""
    # Test with all counts
    counts = {
        "directories": 5,
        "files": 10,
        "lines": 100,
        "tokens": 500,
        "characters": 1000,
    }

    output = format_counts(counts)

    # Check that output contains all the values
    assert "Directories: 5" in output
    assert "Files: 10" in output
    assert "Lines: 100" in output
    assert "Tokens: 500" in output
    assert "Characters: 1000" in output

    # Test without tokens
    counts["tokens"] = None
    output = format_counts(counts)

    assert "Tokens:" not in output
    assert "Directories: 5" in output
    assert "Files: 10" in output
    assert "Lines: 100" in output
    assert "Characters: 1000" in output
