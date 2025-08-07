"""Binary file detection utilities."""

from pathlib import Path

from dir2text.types import PathType

# Common binary file extensions (high confidence)
BINARY_EXTENSIONS = frozenset(
    {
        # Executables
        ".exe",
        ".dll",
        ".so",
        ".class",
        ".bin",
        ".dat",
        # Images
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".psd",
        ".ico",
        ".webp",
        # Videos
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".mpg",
        ".vob",
        ".wmv",
        ".m4v",
        # Audio
        ".mp3",
        ".aac",
        ".wav",
        ".flac",
        ".ogg",
        ".mka",
        ".wma",
        ".m4a",
        # Archives
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".iso",
        ".xz",
        # Database
        ".mdb",
        ".sqlite",
        ".db",
        ".sqlite3",
    }
)

# Common text file extensions (high confidence)
TEXT_EXTENSIONS = frozenset(
    {
        # Source code
        ".py",
        ".js",
        ".html",
        ".css",
        ".xml",
        ".json",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".cs",
        ".rb",
        ".pl",
        ".php",
        ".sh",
        ".go",
        ".rs",
        ".ts",
        ".tsx",
        ".jsx",
        ".vue",
        ".svelte",
        ".scala",
        ".kt",
        ".swift",
        ".m",
        ".mm",
        # Documents/Config
        ".txt",
        ".md",
        ".markdown",
        ".tex",
        ".csv",
        ".tsv",
        ".log",
        ".logs",
        ".ini",
        ".cfg",
        ".conf",
        ".yaml",
        ".yml",
        ".toml",
        ".properties",
        # Web/Markup
        ".htm",
        ".xhtml",
        ".svg",
        ".rss",
        ".atom",
    }
)


def is_binary_file(file_path: PathType, chunk_size: int = 8192) -> bool:
    """Detect if a file is binary using extension hints and content analysis.

    This function uses a two-phase approach:
    1. Fast-path: Check file extension for high-confidence classification
    2. Fallback: Content analysis for unknown/uncertain extensions using:
       - Null byte detection
       - Multi-encoding text validation
       - Control character ratio analysis

    Args:
        file_path: Path to the file to analyze. Can be any path-like object.
        chunk_size: Number of bytes to read for content analysis. Defaults to 8192.

    Returns:
        True if the file appears to be binary, False if it appears to be text.

    Raises:
        OSError: If the file cannot be read.
        FileNotFoundError: If the file doesn't exist.

    Example:
        >>> is_binary_file("README.txt")  # doctest: +SKIP
        False
        >>> is_binary_file("image.png")  # doctest: +SKIP
        True
    """
    path_obj = Path(file_path)

    # Phase 1: Fast-path extension checking for performance optimization
    extension = path_obj.suffix.lower()

    if extension in BINARY_EXTENSIONS:
        return True

    if extension in TEXT_EXTENSIONS:
        return False

    # Phase 2: Content-based analysis for unknown extensions

    # Empty files are considered text
    try:
        if path_obj.stat().st_size == 0:
            return False
    except OSError:
        # If we can't get file stats, let the actual read operation handle the error
        pass

    try:
        with open(path_obj, "rb") as file:
            chunk = file.read(chunk_size)

        # Empty files are text
        if not chunk:
            return False

        # Check for null bytes - common indicator of binary files
        if b"\0" in chunk:
            return True

        # Try to decode with multiple common text encodings
        text_encodings = ["utf-8", "latin-1", "cp1252", "utf-16", "utf-16-le", "utf-16-be"]

        for encoding in text_encodings:
            try:
                chunk.decode(encoding)

                # If we can decode successfully, check for control characters (except common whitespace)
                # Allow common whitespace: tab (9), newline (10), carriage return (13)
                control_chars = sum(1 for byte in chunk if byte < 32 and byte not in (9, 10, 13))

                # If more than 1% are control characters, consider it binary
                if len(chunk) > 0 and control_chars / len(chunk) > 0.01:
                    return True

                return False  # Valid text with minimal control chars = text
            except UnicodeDecodeError:
                # Try next encoding
                continue

        # Fallback: ASCII-based detection when no text encoding works
        # ASCII printable characters are in range 32-126, plus common whitespace (9, 10, 13)
        printable_chars = sum(1 for byte in chunk if byte in range(32, 127) or byte in (9, 10, 13))

        total_chars = len(chunk)
        if total_chars == 0:
            return False

        printable_ratio = printable_chars / total_chars

        # If less than 95% of characters are printable, consider it binary
        return printable_ratio < 0.95

    except OSError:
        # Re-raise OS errors so they can be handled at higher levels
        raise
