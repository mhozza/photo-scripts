from pathlib import Path
import os

# Add more suffixes to this list to find more redundant files.
REDUNDANT_SUFFIXES = ["-Enhanced.dng"]

def register_subcommand(subparsers):
    parser = subparsers.add_parser("find-redundant-dng", help="Find redundant DNG files.")
    parser.add_argument("directory", type=Path, help="Directory to search for redundant DNGs.")
    parser.set_defaults(func=find_redundant_dng)

def find_redundant_dng(args):
    directory = args.directory
    for root, _, files in os.walk(directory):
        for file in files:
            for suffix in REDUNDANT_SUFFIXES:
                if file.lower().endswith(suffix.lower()):
                    dng_path = Path(root) / file
                    base_name = file[:-len(suffix)]
                    cr2_path = Path(root) / (base_name + ".cr2")
                    cr3_path = Path(root) / (base_name + ".cr3")
                    if cr2_path.exists() or cr3_path.exists():
                        print(dng_path)
                        break
