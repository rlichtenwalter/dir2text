import argparse
import sys
from pathlib import Path
from .file_system_tree import FileSystemTree
from .exclusion_rules import GitIgnoreExclusionRules
from .file_content_printer import FileContentPrinter


def main():
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

        def print_output():
            if not args.no_tree:
                print(fs_tree.get_tree_representation())
                if not args.no_contents:
                    print()  # Add newline between tree and contents
            if not args.no_contents:
                printer = FileContentPrinter(fs_tree, wrapper_format=args.format)
                printer.print_all_file_contents()

        if args.output:
            with args.output.open("w") as f:
                sys.stdout = f  # Redirect stdout to the file
                print_output()
                sys.stdout = sys.__stdout__  # Reset stdout
            print(f"Output written to {args.output}")
        else:
            print_output()

        # Check if no output was generated
        if args.no_tree and args.no_contents:
            print("Warning: Both tree and contents printing were disabled. No output generated.", file=sys.stderr)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
