import argparse
import atexit
import errno
import os
import signal
import sys
from pathlib import Path
from threading import Event
from types import FrameType
from typing import Optional, Union

from dir2text.exclusion_rules.git_rules import GitIgnoreExclusionRules
from dir2text.file_content_printer import FileContentPrinter
from dir2text.file_system_tree import FileSystemTree
from dir2text.output_strategies.base_strategy import OutputStrategy
from dir2text.output_strategies.json_strategy import JSONOutputStrategy
from dir2text.output_strategies.xml_strategy import XMLOutputStrategy
from dir2text.token_counter import TokenCounter


class SignalHandler:
    def __init__(self):
        self.sigpipe_received = Event()
        self.sigint_received = Event()
        self.original_sigpipe_handler = signal.getsignal(signal.SIGPIPE)
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)

    def handle_sigpipe(self, signum: int, frame: Optional[FrameType]) -> None:
        self.sigpipe_received.set()
        signal.signal(signal.SIGPIPE, self.original_sigpipe_handler)

    def handle_sigint(self, signum: int, frame: Optional[FrameType]) -> None:
        self.sigint_received.set()
        signal.signal(signal.SIGINT, self.original_sigint_handler)


signal_handler = SignalHandler()


def setup_signal_handling() -> None:
    signal.signal(signal.SIGPIPE, signal_handler.handle_sigpipe)
    signal.signal(signal.SIGINT, signal_handler.handle_sigint)


class SafeWriter:
    def __init__(self, file: Union[int, Path]):
        self.file = file
        self.fd = file if isinstance(file, int) else file.open("w").fileno()

    def write(self, data: str) -> None:
        if signal_handler.sigpipe_received.is_set() or signal_handler.sigint_received.is_set():
            raise BrokenPipeError()
        try:
            os.write(self.fd, data.encode())
        except OSError as e:
            if e.errno == errno.EPIPE:
                raise BrokenPipeError()
            raise

    def close(self) -> None:
        if not isinstance(self.file, int):
            os.close(self.fd)


def cleanup() -> None:
    if signal_handler.sigpipe_received.is_set() or signal_handler.sigint_received.is_set():
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())


atexit.register(cleanup)


def format_counts(counts: dict[str, Optional[int]]) -> str:
    return (
        f"Directories: {counts['directories']}\n"
        f"Files: {counts['files']}\n"
        f"Lines: {counts['lines']}\n"
        f"Characters: {counts['characters']}\n"
        f"Tokens: {counts['tokens'] if counts['tokens'] is not None else 'N/A (tokenizer not available)'}"
    )


def main() -> None:
    setup_signal_handling()

    parser = argparse.ArgumentParser(
        description="Generate a tree representation and print contents of the given directory.",
        epilog="The DIRECTORY argument is required.",
    )
    parser.add_argument("directory", type=Path, help="The directory to process (required)")
    parser.add_argument("-e", "--exclude", type=Path, metavar="FILE", help="Path to exclusion file")
    parser.add_argument("-o", "--output", type=Path, metavar="FILE", help="Output file path")
    parser.add_argument("-T", "--no-tree", action="store_true", help="Do not print the directory tree")
    parser.add_argument("-C", "--no-contents", action="store_true", help="Do not print the contents of files")
    parser.add_argument("--format", choices=["xml", "json"], default="xml", help="Output format for file contents")
    parser.add_argument(
        "-c", "--count", action="store_true", help="Include counts of directories, files, lines, tokens, and characters"
    )
    parser.add_argument("-t", "--tokenizer", default="gpt-4", help="Tokenizer model to use for counting tokens")

    args = parser.parse_args()

    try:
        if not args.directory.is_dir():
            raise ValueError(f"'{args.directory}' is not a valid directory")

        exclusion_rules = None
        if args.exclude:
            if not args.exclude.is_file():
                raise ValueError(f"'{args.exclude}' is not a valid file")
            exclusion_rules = GitIgnoreExclusionRules(args.exclude)

        fs_tree = FileSystemTree(str(args.directory), exclusion_rules)
        token_counter = TokenCounter(model=args.tokenizer) if args.count else None

        output_strategy: OutputStrategy
        if args.format == "xml":
            output_strategy = XMLOutputStrategy()
        elif args.format == "json":
            output_strategy = JSONOutputStrategy()
        else:
            raise ValueError(f"Unsupported output format: {args.format}")

        file_content_printer = FileContentPrinter(fs_tree, output_strategy, tokenizer=token_counter)

        output_file = args.output if args.output else sys.stdout.fileno()
        safe_writer = SafeWriter(output_file)

        try:
            if not args.no_tree:
                tree_repr = fs_tree.get_tree_representation()
                for line in tree_repr.splitlines(True):
                    safe_writer.write(line)
                    if token_counter:
                        token_counter.count_tokens(line)
                safe_writer.write("\n")

                if not args.no_contents:
                    safe_writer.write("\n")

            if not args.no_contents:
                for _, _, content_iterator in file_content_printer.yield_file_contents():
                    for chunk in content_iterator:
                        safe_writer.write(chunk)
                    safe_writer.write("\n")

            if args.count:
                counts = {
                    "directories": fs_tree.get_directory_count(),
                    "files": fs_tree.get_file_count(),
                    "lines": token_counter.get_total_lines() if token_counter else None,
                    "characters": token_counter.get_total_characters() if token_counter else None,
                    "tokens": token_counter.get_total_tokens() if token_counter else None,
                }
                count_output_str = format_counts(counts)
                safe_writer.write("\n" + count_output_str + "\n")

            if args.no_tree and args.no_contents and not args.count:
                print(
                    "Warning: Both tree and contents printing were disabled, and counting was not enabled.",
                    end="",
                    file=sys.stderr,
                )
                print(" No output generated.", file=sys.stderr)

        except BrokenPipeError:
            pass  # We'll handle the exit in the finally block
        finally:
            safe_writer.close()

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # Handle exit codes here, after all cleanup has been performed
    if signal_handler.sigpipe_received.is_set():
        sys.exit(141)
    elif signal_handler.sigint_received.is_set():
        sys.exit(130)


if __name__ == "__main__":
    main()
