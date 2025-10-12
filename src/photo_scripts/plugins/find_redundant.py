from pathlib import Path
import os
import sys
from photo_scripts.libs.files import move_file

# Add more suffixes to this list to find more redundant files.
REDUNDANT_SUFFIXES = ["-Enhanced-NR.dng"]

def register_subcommand(subparsers):
    parser = subparsers.add_parser("find-redundant", help="Find redundant image files.")
    parser.add_argument("directory", type=Path, help="Directory to search for redundant files.")
    parser.add_argument("--move", type=Path, help="Move redundant files to the specified directory.")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually move files, just show what would be done.")
    parser.set_defaults(func=find_redundant)

def find_redundant(args):
    directory = args.directory
    move_destination = args.move
    dry_run = args.dry_run
    file_count = 0
    redundant_file_count = 0
    moved_file_count = 0
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
                        redundant_file_count += 1
                        if move_destination:
                            if move_file(path, directory, move_destination, dry_run):
                                moved_file_count += 1
                        else:
                            print(path)
                        break
    print(f"Scanned {file_count} files.", file=sys.stderr)
    print(f"Found {redundant_file_count} redundant files.", file=sys.stderr)
    if move_destination:
        print(f"Moved {moved_file_count} files.", file=sys.stderr)