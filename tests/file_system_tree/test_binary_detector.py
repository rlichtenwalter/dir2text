"""Tests for binary file detection functionality."""

import tempfile
from pathlib import Path

import pytest

from dir2text.file_system_tree.binary_detector import BINARY_EXTENSIONS, TEXT_EXTENSIONS, is_binary_file


class TestBinaryFileDetection:
    """Test binary file detection logic."""

    def test_empty_file_is_text(self):
        """Test that empty files are considered text."""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = Path(temp_file.name)
            assert not is_binary_file(temp_path)

    def test_text_file_detection(self):
        """Test detection of text files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("Hello, world!\nThis is a text file.\n")
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            assert not is_binary_file(temp_path)
        finally:
            temp_path.unlink()

    def test_binary_file_with_null_bytes(self):
        """Test detection of binary files containing null bytes."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write some text with null bytes (common in binary files)
            temp_file.write(b"Hello\x00World\x00\x01\x02\x03")
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            assert is_binary_file(temp_path)
        finally:
            temp_path.unlink()

    def test_binary_file_with_high_ratio_non_printable(self):
        """Test detection of binary files with high ratio of non-printable characters."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write mostly non-printable bytes
            binary_data = bytes(range(0, 128)) + b"Some text"
            temp_file.write(binary_data)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            assert is_binary_file(temp_path)
        finally:
            temp_path.unlink()

    def test_text_with_some_non_printable(self):
        """Test that text files with some non-printable chars are still considered text."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Mix of printable text with occasional non-printable (but below 5% threshold)
            text_data = b"This is mostly text content with tabs\t and newlines\n" * 100
            # Add a small amount of non-printable data (less than 5%)
            mixed_data = text_data + b"\x80\x81\x82"
            temp_file.write(mixed_data)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            assert not is_binary_file(temp_path)
        finally:
            temp_path.unlink()

    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for non-existent files with unknown extensions."""
        # Use unknown extension so it falls back to content analysis
        non_existent_path = Path("/path/that/does/not/exist.unknownext")
        with pytest.raises(OSError):
            is_binary_file(non_existent_path)

    def test_custom_chunk_size(self):
        """Test binary detection with custom chunk size."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Hi\x00World")  # Null byte within first 4 bytes
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            # Should still detect as binary regardless of chunk size
            assert is_binary_file(temp_path, chunk_size=4)
            assert is_binary_file(temp_path, chunk_size=1024)
        finally:
            temp_path.unlink()


class TestFileExtensionHeuristics:
    """Test file extension-based text file detection."""

    def test_extension_based_text_detection(self):
        """Test that files with text extensions are detected as text without file I/O."""
        text_extensions = [
            "file.txt",
            "README.md",
            "script.py",
            "style.css",
            "data.json",
            "config.yml",
            "settings.toml",
            "app.js",
            "page.html",
            "doc.xml",
        ]

        for filename in text_extensions:
            # Create a path that doesn't exist - extension detection should work without file I/O
            fake_path = Path("/nonexistent") / filename
            extension = fake_path.suffix.lower()
            assert extension in TEXT_EXTENSIONS, f"{filename} extension should be in TEXT_EXTENSIONS"

    def test_extension_based_binary_detection(self):
        """Test that files with binary extensions are detected as binary without file I/O."""
        binary_extensions = [
            "image.jpg",
            "photo.png",
            "video.mp4",
            "audio.mp3",
            "app.exe",
            "lib.so",
            "archive.zip",
            "data.db",
            "image.gif",
        ]

        for filename in binary_extensions:
            # Create a path that doesn't exist - extension detection should work without file I/O
            fake_path = Path("/nonexistent") / filename
            extension = fake_path.suffix.lower()
            assert extension in BINARY_EXTENSIONS, f"{filename} extension should be in BINARY_EXTENSIONS"

    def test_case_insensitive_extensions(self):
        """Test that extension detection is case insensitive."""
        # Test uppercase extensions are handled correctly
        assert Path("FILE.TXT").suffix.lower() in TEXT_EXTENSIONS
        assert Path("Script.PY").suffix.lower() in TEXT_EXTENSIONS
        assert Path("IMAGE.JPG").suffix.lower() in BINARY_EXTENSIONS

    def test_no_extension_fallback_to_content_analysis(self):
        """Test that files with no extension use content analysis."""
        # Files without extensions should not be in either extension set
        assert Path("filename_with_no_extension").suffix.lower() not in TEXT_EXTENSIONS
        assert Path("filename_with_no_extension").suffix.lower() not in BINARY_EXTENSIONS
        assert Path("README").suffix.lower() not in TEXT_EXTENSIONS  # No extension
        assert Path("README").suffix.lower() not in BINARY_EXTENSIONS

    def test_programming_language_extensions(self):
        """Test that programming language file extensions are recognized."""
        programming_files = [
            "main.c",
            "app.cpp",
            "util.h",
            "Service.java",
            "script.sh",
            "program.go",
            "module.rs",
            "app.kt",
            "view.swift",
            "build.scala",
        ]

        for filename in programming_files:
            extension = Path(filename).suffix.lower()
            assert extension in TEXT_EXTENSIONS, f"{filename} extension should be in TEXT_EXTENSIONS"


class TestExtensionOptimization:
    """Test the extension-based performance optimization."""

    def test_binary_extension_fast_path(self):
        """Test that known binary extensions return True without file I/O."""
        # Create path to non-existent file with binary extension
        nonexistent_binary = Path("/nonexistent/test.jpg")

        # Should return True based purely on extension (no file I/O)
        # This would raise FileNotFoundError if content analysis was attempted
        assert is_binary_file(nonexistent_binary) is True

    def test_text_extension_fast_path(self):
        """Test that known text extensions return False without file I/O."""
        # Create path to non-existent file with text extension
        nonexistent_text = Path("/nonexistent/test.py")

        # Should return False based purely on extension (no file I/O)
        # This would raise FileNotFoundError if content analysis was attempted
        assert is_binary_file(nonexistent_text) is False

    def test_unknown_extension_falls_back_to_content_analysis(self):
        """Test that unknown extensions trigger content analysis."""
        # Create path with unknown extension - should attempt file I/O and fail
        nonexistent_unknown = Path("/nonexistent/test.unknownext")

        with pytest.raises(FileNotFoundError):
            is_binary_file(nonexistent_unknown)

    def test_no_extension_falls_back_to_content_analysis(self):
        """Test that files without extensions trigger content analysis."""
        # Create path without extension - should attempt file I/O and fail
        nonexistent_no_ext = Path("/nonexistent/README")

        with pytest.raises(FileNotFoundError):
            is_binary_file(nonexistent_no_ext)

    def test_extension_case_insensitive_optimization(self):
        """Test that extension checking is case insensitive."""
        # Test various case combinations
        assert is_binary_file(Path("/nonexistent/test.JPG")) is True
        assert is_binary_file(Path("/nonexistent/test.Jpg")) is True
        assert is_binary_file(Path("/nonexistent/test.jPg")) is True

        assert is_binary_file(Path("/nonexistent/test.PY")) is False
        assert is_binary_file(Path("/nonexistent/test.Py")) is False
        assert is_binary_file(Path("/nonexistent/test.pY")) is False
