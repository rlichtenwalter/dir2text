#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Function to print usage information
print_usage() {
    cat << EOF
Usage: $0 [-f EXCLUSION_FILE | -e EXCLUSION_LIST] DIRECTORY
Generate a file system tree representation and file contents.
Options:
  -f EXCLUSION_FILE    File containing exclusion glob patterns, one per line
  -e EXCLUSION_LIST    Comma-separated list of exclusion glob patterns
  DIRECTORY            The directory to process
Note: You can use either -f or -e, but not both. If neither is provided, no exclusions will be applied.
EOF
}

# Function to convert glob patterns to find exclusion flags
convert_to_find_flags() {
    local patterns=("$@")
    local find_flags=()
    for pattern in "${patterns[@]}"; do
        find_flags+=(-not -path "$pattern")
    done
    printf '%s\n' "${find_flags[@]}"
}

# Function to sanitize path for XML element
sanitize_path() {
    echo "$1" | sed -e 's/[^[:alnum:]]/_/g' | sed -e 's/^[0-9]/_&/'
}

# Parse command-line arguments
EXCLUSION_FILE=""
EXCLUSION_LIST=""

# Check if there are any arguments
if [ $# -eq 0 ]; then
    echo "Error: No arguments provided." >&2
    print_usage
    exit 1
fi

# Parse options
while getopts ":f:e:h" opt; do
    case ${opt} in
        f)
            EXCLUSION_FILE=$OPTARG
            ;;
        e)
            EXCLUSION_LIST=$OPTARG
            ;;
        h)
            print_usage
            exit 0
            ;;
        \?)
            echo "Error: Invalid option: -$OPTARG" >&2
            print_usage
            exit 1
            ;;
        :)
            echo "Error: Option -$OPTARG requires an argument." >&2
            print_usage
            exit 1
            ;;
    esac
done

# Check if there are any non-option arguments left
if [ $OPTIND -gt $# ]; then
    echo "Error: Directory argument is required." >&2
    print_usage
    exit 1
fi

# Shift to the next non-option argument
shift $((OPTIND -1))

# Check if there are any unexpected arguments
if [ $# -gt 1 ]; then
    echo "Error: Too many arguments. Only one directory expected." >&2
    print_usage
    exit 1
fi

# Check that only one of -e or -f is provided
if [ -n "$EXCLUSION_FILE" ] && [ -n "$EXCLUSION_LIST" ]; then
    echo "Error: You can use either -f or -e, but not both." >&2
    print_usage
    exit 1
fi

DIRECTORY=$1

# Process exclusion patterns
EXCLUSION_PATTERNS=()
if [ -n "$EXCLUSION_FILE" ]; then
    if [ ! -f "$EXCLUSION_FILE" ]; then
        echo "Error: Exclusion file not found: $EXCLUSION_FILE" >&2
        exit 1
    fi
    mapfile -t EXCLUSION_PATTERNS < "$EXCLUSION_FILE"
elif [ -n "$EXCLUSION_LIST" ]; then
    IFS=',' read -ra EXCLUSION_PATTERNS <<< "$EXCLUSION_LIST"
fi

# Convert exclusion patterns to find flags
FIND_FLAGS=()
if [ ${#EXCLUSION_PATTERNS[@]} -gt 0 ]; then
    readarray -t FIND_FLAGS < <(convert_to_find_flags "${EXCLUSION_PATTERNS[@]}")
fi

# Function to run find command with or without exclusion flags
run_find() {
    local dir=$1
    shift
    if [ $# -eq 0 ]; then
        find "$dir" -printf '%P\n'
    else
        find "$dir" "$@" -printf '%P\n'
    fi
}

# Generate tree output
tree_output=$(run_find "$DIRECTORY" "${FIND_FLAGS[@]+"${FIND_FLAGS[@]}"}" | sort | grep -v '^$' | sed -e "s/[^-][^\/]*\// |/g" -e "s/|\([^ ]\)/|-\1/" -e "s/^ //")
printf "%s\n" "$tree_output"

# Process and print file contents
while IFS= read -r file; do
    if [ -f "$DIRECTORY/$file" ]; then
        sanitized_path=$(sanitize_path "$file")
        printf "\n%s: <%s>\n" "$file" "$sanitized_path"
        cat "$DIRECTORY/$file"
        printf "</%s>\n" "$sanitized_path"
    fi
done < <(run_find "$DIRECTORY" "${FIND_FLAGS[@]+"${FIND_FLAGS[@]}"}" -type f)

