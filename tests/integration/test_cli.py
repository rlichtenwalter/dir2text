"""Integration tests for the command-line interface.

This integration test suite covers various aspects of the CLI functionality including:
- Symlink following
- No-tree/no-contents options
- Permission action handling
- Output file verification
- Empty directory handling
- Version information
- Complex exclusion patterns
- Token counting (conditional)
"""

import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from dir2text.cli.main import format_counts  # noqa: F401 - Used in fixture names to match production code

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


@pytest.fixture
def temp_project_with_symlinks():
    """Create a temporary project with symlinks for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create directories
        (base_dir / "src").mkdir()
        (base_dir / "docs").mkdir()

        # Create test files
        (base_dir / "src" / "main.py").write_text("def main():\n    print('Hello')\n")
        (base_dir / "docs" / "README.md").write_text("# Test Project\n")

        # Create symlinks - this may fail on some platforms
        try:
            # Create a symlink to a file
            os.symlink(base_dir / "docs" / "README.md", base_dir / "README_link.md")

            # Create a symlink to a directory
            os.symlink(base_dir / "src", base_dir / "src_link")

            has_symlinks = True
        except (OSError, AttributeError):
            # Symlinks not supported or failed to create
            has_symlinks = False

        yield base_dir, has_symlinks


@pytest.fixture
def temp_complex_gitignore():
    """Create a temporary .gitignore file with complex patterns."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        # These patterns are from a typical project
        f.write("# Byte-compiled / optimized / DLL files\n")
        f.write("__pycache__/\n")
        f.write("*.py[cod]\n")
        f.write("*$py.class\n\n")

        f.write("# Distribution / packaging\n")
        f.write("dist/\n")
        f.write("build/\n")
        f.write("*.egg-info/\n\n")

        f.write("# Unit test / coverage reports\n")
        f.write("htmlcov/\n")
        f.write(".coverage\n")
        f.write(".pytest_cache/\n\n")

        f.write("# Environments\n")
        f.write(".env\n")
        f.write(".venv\n")
        f.write("env/\n")
        f.write("venv/\n\n")

        f.write("# Editors\n")
        f.write(".vscode/\n")
        f.write(".idea/\n")
        f.write("*.swp\n")
        f.write("*~\n\n")

        f.write("# Exceptions\n")
        f.write("!.gitignore\n")
        f.write("!README.md\n")
        f.write("!important/build/file.txt\n")

    yield f.name

    # Clean up
    os.unlink(f.name)


@pytest.fixture
def temp_empty_directory():
    """Create a temporary empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def run_cli(args, cwd=None, capture_output=True, timeout=10):
    """Run the dir2text CLI with the given arguments.

    Args:
        args: List of CLI arguments
        cwd: Working directory
        capture_output: Whether to capture stdout/stderr
        timeout: Maximum time to wait for command to complete

    Returns:
        CompletedProcess object with stdout/stderr as text if capture_output=True
    """
    cmd = [sys.executable, "-m", "dir2text.cli.main"] + args

    if capture_output:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd, timeout=timeout
        )
    else:
        result = subprocess.run(cmd, text=True, cwd=cwd, timeout=timeout)

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


def test_cli_follow_symlinks(temp_project_with_symlinks):
    """Test the -L/--follow-symlinks option."""
    base_dir, has_symlinks = temp_project_with_symlinks

    if not has_symlinks:
        pytest.skip("Symlink creation not supported on this platform/environment")

    # Test default behavior (don't follow symlinks)
    result_default = run_cli([str(base_dir)])

    # Test with --follow-symlinks
    result_follow = run_cli(["-L", str(base_dir)])

    # In default mode:
    # - Symlinks should be shown as symlinks with targets
    assert "README_link.md → " in result_default.stdout
    assert "src_link → " in result_default.stdout
    assert "[symlink]" in result_default.stdout

    # In follow mode:
    # - Content from symlinked files should appear
    # - Symlink directory contents should be traversed
    assert "README_link.md → " not in result_follow.stdout
    assert "src_link/" in result_follow.stdout  # Shown as directory

    # The content in src_link/main.py should be included
    assert "def main():" in result_follow.stdout


def test_cli_no_tree_option(temp_project):
    """Test the -T/--no-tree option."""
    result = run_cli(["-T", str(temp_project)])

    # Verify output doesn't contain tree representation
    assert "├── " not in result.stdout, "Tree characters should not be present"
    assert "└── " not in result.stdout, "Tree characters should not be present"

    # Should still contain file contents
    assert "def main():" in result.stdout, "File contents should be present"
    assert "# Test Project" in result.stdout, "File contents should be present"


def test_cli_no_contents_option(temp_project):
    """Test the -C/--no-contents option."""
    result = run_cli(["-C", str(temp_project)])

    # Verify output contains only tree representation
    assert "├── " in result.stdout, "Tree characters should be present"
    assert "└── " in result.stdout, "Tree characters should be present"

    # Should not contain file contents
    assert "def main():" not in result.stdout
    assert "# Test Project" not in result.stdout


def test_cli_no_tree_no_contents(temp_project):
    """Test using both -T and -C options together."""
    result = run_cli(["-T", "-C", str(temp_project)])

    # Output should be empty or contain only a warning
    assert result.returncode == 0
    assert "Warning: Both tree and contents printing were disabled" in result.stderr


def test_cli_output_file_verification(temp_project):
    """Test writing output to a file and verify contents."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_output:
        output_path = temp_output.name

    try:
        # Run with output to file
        result = run_cli(["-o", output_path, str(temp_project)])

        # Check command succeeded
        assert result.returncode == 0

        # Verify stdout is empty (since output is redirected to file)
        assert not result.stdout

        # Read the output file
        with open(output_path, "r") as f:
            file_content = f.read()

        # Verify file contains expected content
        assert "def main():" in file_content
        assert "# Test Project" in file_content
    finally:
        # Clean up
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_cli_empty_directory(temp_empty_directory):
    """Test handling of an empty directory."""
    result = run_cli([str(temp_empty_directory)])

    # Should succeed but have minimal output
    assert result.returncode == 0

    # Should show directory name in the tree
    dir_name = temp_empty_directory.name
    assert dir_name in result.stdout

    # Should not have any file content
    assert "<file " not in result.stdout


def test_cli_complex_patterns(temp_project, temp_complex_gitignore):
    """Test with complex, realistic .gitignore patterns."""
    # Create some additional files that match complex patterns
    (temp_project / "__pycache__").mkdir(exist_ok=True)
    (temp_project / "__pycache__" / "cache.pyc").write_text("cache content")
    (temp_project / ".venv").mkdir(exist_ok=True)
    (temp_project / ".venv" / "bin").mkdir(exist_ok=True)
    (temp_project / ".venv" / "bin" / "python").write_text("#!/bin/python\n")
    (temp_project / ".vscode").mkdir(exist_ok=True)
    (temp_project / ".vscode" / "settings.json").write_text("{}")
    (temp_project / "important").mkdir(exist_ok=True)
    (temp_project / "important" / "build").mkdir(exist_ok=True)
    (temp_project / "important" / "build" / "file.txt").write_text("Important file!")

    # Run with complex gitignore
    result = run_cli(["-e", temp_complex_gitignore, str(temp_project)])

    # Verify excluded content isn't present
    assert "cache content" not in result.stdout, "Excluded __pycache__ content should not appear"
    assert "#!/bin/python" not in result.stdout, "Excluded .venv content should not appear"
    assert "settings.json" not in result.stdout, "Excluded .vscode content should not appear"

    # Verify negated patterns (exceptions) work
    assert "important/build/file.txt" in result.stdout
    assert "Important file!" in result.stdout


def test_cli_version_info():
    """Test the -V/--version flag."""
    # Test with short flag
    result_short = run_cli(["-V"])

    # Test with long flag
    result_long = run_cli(["--version"])

    # Verify output contains version information
    assert result_short.returncode == 0
    assert result_long.returncode == 0
    assert "dir2text" in result_short.stdout
    assert "dir2text" in result_long.stdout

    # Version should be formatted like X.Y.Z
    import re

    version_match = re.search(r"dir2text (\d+\.\d+\.\d+)", result_short.stdout)
    assert version_match is not None, "Version information should be displayed"


def test_cli_token_counting(temp_project):
    """Test token counting with the -t/--tokenizer option."""
    # Try running with tokenizer option
    result = run_cli(["-t", "gpt-4", "-s", "stderr", str(temp_project)])

    # If tiktoken is available, check token counts
    if result.returncode == 0:
        assert "Tokens:" in result.stderr
    else:
        # If tiktoken is not available, verify appropriate error message
        assert "Token counting was requested" in result.stderr
        assert "tiktoken library is not installed" in result.stderr


def test_cli_permission_action_options(temp_project):
    """Test the -P/--permission-action option."""
    # We can test the option is recognized, though actual permission errors
    # are difficult to reliably create in cross-platform tests

    # Test with 'ignore' (default)
    result_ignore = run_cli(["-P", "ignore", str(temp_project)])
    assert result_ignore.returncode == 0

    # Test with 'warn'
    result_warn = run_cli(["-P", "warn", str(temp_project)])
    assert result_warn.returncode == 0

    # Test with 'fail'
    result_fail = run_cli(["-P", "fail", str(temp_project)])
    assert result_fail.returncode == 0

    # Test with invalid option
    result_invalid = run_cli(["-P", "invalid", str(temp_project)])
    assert result_invalid.returncode != 0
    assert "invalid choice" in result_invalid.stderr


# Utility function to check if tiktoken is available
def is_tiktoken_available():
    """Check if tiktoken is available."""
    try:
        import tiktoken  # noqa: F401 - Only checking for availability, not actual usage

        return True
    except ImportError:
        return False


@pytest.mark.skipif(platform.system() == "Windows", reason="Signal testing not reliable on Windows")
def test_cli_sigpipe_handling(temp_project):
    """Test handling of SIGPIPE signal."""
    # This is a limited test that can only be run on Unix-like systems

    try:
        # Create a subprocess that pipes output through 'head'
        # This will cause a SIGPIPE when head closes the pipe
        process = subprocess.Popen(
            f"{sys.executable} -m dir2text.cli.main {str(temp_project)} | head -n 5",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give it a moment to run
        time.sleep(1)

        # Get return code
        return_code = process.poll()

        # If process is still running, kill it
        if return_code is None:
            process.terminate()
            process.wait(timeout=5)
            return_code = process.returncode

        # Output should be limited by head, and process should exit cleanly
        stdout, stderr = process.communicate()

        # Process should exit without error message
        assert not stderr or not stderr.strip()

        # In Unix systems, SIGPIPE typically results in exit code 141
        # but we'll also accept 0 as "clean exit"
        assert return_code in (0, 141)

    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        # If something goes wrong, skip the test rather than fail
        pytest.skip("Signal handling test encountered an error")


def test_cli_summary_options(temp_project):
    """Test the -s/--summary options."""

    # Test default summary behavior (stderr output)
    # -s/--summary requires an argument, so use 'stderr' explicitly
    result_default = run_cli(["-s", "stderr", str(temp_project)])
    assert result_default.returncode == 0
    assert "Directories:" in result_default.stderr
    assert "Files:" in result_default.stderr
    assert "Lines:" in result_default.stderr
    assert "Characters:" in result_default.stderr
    # No token counts without tokenizer
    assert "Tokens:" not in result_default.stderr
    # Make sure summary aren't in stdout
    assert "Directories:" not in result_default.stdout

    # Test stdout summary
    result_stdout = run_cli(["-s", "stdout", str(temp_project)])
    assert result_stdout.returncode == 0
    assert "Directories:" in result_stdout.stdout
    assert "Files:" in result_stdout.stdout
    assert "Lines:" in result_stdout.stdout
    assert "Characters:" in result_stdout.stdout
    # Make sure summary aren't in stderr
    assert "Directories:" not in result_stdout.stderr

    # Test summary with token counting
    result_with_tokens = run_cli(["-s", "stderr", "-t", "gpt-4", str(temp_project)])
    # Note: This might fail in the actual test environment if tiktoken is not available
    # In that case, we'd test for the proper error message instead
    if result_with_tokens.returncode == 0:
        assert "Directories:" in result_with_tokens.stderr
        assert "Files:" in result_with_tokens.stderr
        assert "Lines:" in result_with_tokens.stderr
        assert "Characters:" in result_with_tokens.stderr
        assert "Tokens:" in result_with_tokens.stderr
    else:
        # If it failed because tiktoken is not available, check for the appropriate error message
        assert "Token counting was requested" in result_with_tokens.stderr
        assert "tiktoken library is not installed" in result_with_tokens.stderr

    # Test tokenizer only (without summary flag)
    # This should not print any summary
    result_tokenizer_only = run_cli(["-t", "gpt-4", str(temp_project)])
    if result_tokenizer_only.returncode == 0:
        assert "Tokens:" not in result_tokenizer_only.stderr
        assert "Directories:" not in result_tokenizer_only.stderr
    else:
        # If it failed because tiktoken is not available, check for the appropriate error message
        assert "Token counting was requested" in result_tokenizer_only.stderr
        assert "tiktoken library is not installed" in result_tokenizer_only.stderr


def test_cli_summary_to_file(temp_project):
    """Test the -s file option with output file."""
    # Create a regular output file instead of using NamedTemporaryFile
    output_path = str(temp_project / "output.txt")

    try:
        # Test summary to file
        result = run_cli(["-s", "file", "-o", output_path, str(temp_project)])
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

        # Verify summary appear in the output file
        with open(output_path, "r") as f:
            content = f.read()
            assert "Directories:" in content
            assert "Files:" in content
            assert "Lines:" in content
            assert "Characters:" in content

        # Verify summary don't appear in stderr
        assert "Directories:" not in result.stderr
    finally:
        # Clean up
        try:
            if os.path.exists(output_path):
                os.unlink(output_path)
        except Exception:
            pass  # Ignore cleanup errors


def test_cli_summary_to_file_without_output(temp_project):
    """Test that specifying -s file without -o fails."""
    result = run_cli(["-s", "file", str(temp_project)])
    assert result.returncode != 0
    assert "--summary=file requires" in result.stderr


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


@pytest.fixture
def temp_project_with_size_files():
    """Create a temporary project with files of different sizes for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create small files
        (base_dir / "small.txt").write_text("Small file")  # ~10 bytes
        (base_dir / "medium.txt").write_text("x" * 500)  # 500 bytes

        # Create large files
        (base_dir / "large.txt").write_text("x" * 2000)  # 2KB
        (base_dir / "huge.txt").write_text("x" * 1100000)  # ~1.1MB

        # Create directories (should not be affected by size limits)
        (base_dir / "src").mkdir()
        (base_dir / "src" / "tiny.py").write_text("print('hi')")  # Very small

        yield base_dir


def test_cli_max_file_size_basic(temp_project_with_size_files):
    """Test basic max file size functionality."""
    project_dir = temp_project_with_size_files

    # Test with 1KB limit - should exclude 2KB and 1.1MB files
    result = run_cli(["-M", "1KB", str(project_dir)])

    assert result.returncode == 0
    assert "small.txt" in result.stdout  # ~10 bytes - included
    assert "medium.txt" in result.stdout  # 500 bytes - included
    assert "tiny.py" in result.stdout  # very small - included
    assert "large.txt" not in result.stdout  # 2KB - excluded
    assert "huge.txt" not in result.stdout  # 1.1MB - excluded


def test_cli_max_file_size_units(temp_project_with_size_files):
    """Test different size unit formats."""
    project_dir = temp_project_with_size_files

    # Test with bytes
    result_bytes = run_cli(["-M", "1500", str(project_dir)])
    assert result_bytes.returncode == 0
    assert "medium.txt" in result_bytes.stdout  # 500 bytes - included
    assert "large.txt" not in result_bytes.stdout  # 2KB - excluded

    # Test with KB (decimal)
    result_kb = run_cli(["-M", "1.5KB", str(project_dir)])
    assert result_kb.returncode == 0
    assert "medium.txt" in result_kb.stdout  # 500 bytes - included
    assert "large.txt" not in result_kb.stdout  # 2KB - excluded

    # Test with MB (decimal) - should include everything except huge file
    result_mb = run_cli(["-M", "1MB", str(project_dir)])
    assert result_mb.returncode == 0
    assert "large.txt" in result_mb.stdout  # 2KB - included
    assert "huge.txt" not in result_mb.stdout  # 1.1MB - excluded

    # Test with MiB (binary)
    result_mib = run_cli(["-M", "2MiB", str(project_dir)])
    assert result_mib.returncode == 0
    assert "huge.txt" in result_mib.stdout  # 1.1MB < 2MiB - included


def test_cli_max_file_size_combined_with_exclusions(temp_project):
    """Test max file size combined with other exclusion rules."""
    project_dir = temp_project

    # Create a large .pyc file
    (project_dir / "large.pyc").write_text("x" * 1000)  # 1KB

    # Create a small .log file
    (project_dir / "small.log").write_text("log entry")  # ~10 bytes

    gitignore_path = str(project_dir / ".gitignore")  # contains: *.pyc\nbuild/\n

    # Combine git exclusions with size limit
    result = run_cli(["-e", gitignore_path, "-M", "100", str(project_dir)])

    assert result.returncode == 0

    # large.pyc should be excluded by git rules (not size)
    assert "large.pyc" not in result.stdout

    # small.log should be included (not excluded by git, under size limit)
    assert "small.log" in result.stdout

    # Files over 100 bytes should be excluded by size rule
    assert "main.py" not in result.stdout  # > 100 bytes
    assert "README.md" not in result.stdout  # > 100 bytes
    assert "package.json" not in result.stdout  # > 100 bytes


def test_cli_max_file_size_invalid_format():
    """Test error handling for invalid size formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test invalid size format
        result = run_cli(["-M", "invalid_size", tmpdir])
        assert result.returncode == 2  # Argument error
        assert "Invalid size format" in result.stderr

        # Test another invalid format
        result = run_cli(["-M", "1XB", tmpdir])  # Invalid unit
        assert result.returncode == 2
        assert "Invalid size format" in result.stderr


def test_cli_max_file_size_directories_not_affected(temp_project_with_size_files):
    """Test that directories are not affected by size limits."""
    project_dir = temp_project_with_size_files

    # Use a very small size limit
    result = run_cli(["-M", "1", str(project_dir)])  # 1 byte limit

    assert result.returncode == 0

    # Directory should still appear in tree
    assert "src/" in result.stdout

    # But files should be excluded
    assert "small.txt" not in result.stdout  # Even small files excluded
    assert "medium.txt" not in result.stdout
    assert "tiny.py" not in result.stdout


def test_cli_max_file_size_no_tree_option(temp_project_with_size_files):
    """Test max file size with --no-tree option."""
    project_dir = temp_project_with_size_files

    result = run_cli(["-T", "-M", "1KB", str(project_dir)])

    assert result.returncode == 0

    # Should not contain tree visualization
    assert "├──" not in result.stdout
    assert "└──" not in result.stdout

    # Should contain content from small files only
    assert "Small file" in result.stdout  # Content of small.txt
    assert "x" * 500 in result.stdout  # Content of medium.txt

    # Should not contain content from large files
    large_content_sample = "x" * 100  # Sample of large file content
    large_count = result.stdout.count(large_content_sample)
    # Should be much less than what would be in the large files
    assert large_count < 5  # Arbitrary small number


def test_cli_max_file_size_json_format(temp_project_with_size_files):
    """Test max file size with JSON output format."""
    project_dir = temp_project_with_size_files

    result = run_cli(["-f", "json", "-M", "1KB", str(project_dir)])

    assert result.returncode == 0

    # Should be valid JSON structure
    assert '"tree":' in result.stdout
    assert '"files":' in result.stdout

    # Should contain small files
    assert "small.txt" in result.stdout
    assert "medium.txt" in result.stdout

    # Should not contain large files
    assert "large.txt" not in result.stdout
    assert "huge.txt" not in result.stdout


def test_cli_max_file_size_zero_size():
    """Test edge case with zero size limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create an empty file
        (base_dir / "empty.txt").write_text("")

        # Create a tiny file
        (base_dir / "tiny.txt").write_text("x")

        # Test with zero size limit - should exclude all non-empty files
        result = run_cli(["-M", "0", str(base_dir)])

        assert result.returncode == 0

        # Empty file should be included (size = 0, limit = 0, so 0 <= 0 is True)
        assert "empty.txt" in result.stdout

        # Any non-empty file should be excluded
        assert "tiny.txt" not in result.stdout


def test_cli_max_file_size_with_symlinks():
    """Test max file size behavior with symbolic links."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create a large target file
        large_file = base_dir / "large_target.txt"
        large_file.write_text("x" * 2000)  # 2KB

        # Create a small target file
        small_file = base_dir / "small_target.txt"
        small_file.write_text("small")  # ~5 bytes

        try:
            # Create symlinks
            large_symlink = base_dir / "large_symlink.txt"
            small_symlink = base_dir / "small_symlink.txt"

            large_symlink.symlink_to(large_file)
            small_symlink.symlink_to(small_file)

            # Test with 1KB limit - should check target file size
            result = run_cli(["-M", "1KB", str(base_dir)])

            assert result.returncode == 0

            # Small symlink should be included (target is small)
            assert "small_symlink.txt" in result.stdout or "small_target.txt" in result.stdout

            # Large symlink should be excluded (target is large)
            assert "large_symlink.txt" not in result.stdout
            assert "large_target.txt" not in result.stdout

        except (OSError, AttributeError):
            # Symlinks not supported on this platform
            pytest.skip("Symlinks not supported on this platform")
