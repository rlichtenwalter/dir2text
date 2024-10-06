import argparse
import sys
from pathlib import Path
from .file_system_tree import FileSystemTree
from .exclusion_rules import GitIgnoreExclusionRules


def main():
    parser = argparse.ArgumentParser(
        description="Generate a tree representation of the given directory.",
        epilog="The DIRECTORY argument is required.",
    )
    parser.add_argument("directory", type=Path, help="The directory to generate the tree for (required)")
    parser.add_argument("-e", "--exclude", type=Path, metavar="FILE", help="Path to exclusion file")
    parser.add_argument("-o", "--output", type=Path, metavar="FILE", help="Output file path")

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
        tree_output = fs_tree.get_tree_representation()

        if args.output:
            args.output.write_text(tree_output)
            print(f"Tree output written to {args.output}")
        else:
            print(tree_output)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
