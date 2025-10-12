from pathlib import Path
import os
import sys

# Add more suffixes to this list to find more redundant files.
REDUNDANT_SUFFIXES = ["-Enhanced-NR.dng"]

def register_subcommand(subparsers):
    parser = subparsers.add_parser("find-redundant", help="Find redundant image files.")
    parser.add_argument("directory", type=Path, help="Directory to search for redundant files.")
    parser.set_defaults(func=find_redundant)

def find_redundant(args):
    directory = args.directory
    file_count = 0
    redundant_file_count = 0
    # os.walk recursively searches the directory tree.
    for root, _, files in os.walk(directory):
        for file in files:
            file_count += 1
            for suffix in REDUNDANT_SUFFIXES:
                if file.lower().endswith(suffix.lower()):
                    path = Path(root) / file
                    base_name = file[:-len(suffix)]
                    cr2_path = Path(root) / (base_name + ".cr2")
                    cr3_path = Path(root) / (base_name + ".cr3")
                    if cr2_path.exists() or cr3_path.exists():
                        print(path)
                        redundant_file_count += 1
                        break
    print(f"Scanned {file_count} files.", file=sys.stderr)
    print(f"Found {redundant_file_count} redundant files.", file=sys.stderr)
