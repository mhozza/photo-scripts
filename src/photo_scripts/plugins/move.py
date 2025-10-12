import argparse
import sys
from pathlib import Path
from photo_scripts.libs.files import move_file

def register_subcommand(subparsers):
    parser = subparsers.add_parser("move", help="Move photos based on a file list.")
    parser.add_argument("-s", "--source", required=True, type=Path, help="Source directory of photos.")
    parser.add_argument("-d", "--destination", required=True, type=Path, help="Destination directory to move photos to.")
    parser.add_argument("-r", "--remove-prefix", type=Path, help="Remove prefix from files")
    parser.add_argument("-f", "--file", required=True, help="File with a list of photos to move")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually move files")
    parser.set_defaults(func=move_photos)

def process_file_line(fname, src, remove_prefix=None):
    fname = Path(fname.strip())

    if remove_prefix is not None and fname.is_relative_to(remove_prefix):
        fname = fname.relative_to(remove_prefix)

    if not fname.is_relative_to(src):
        srcfname = src / fname
    else:
        srcfname = fname

    if not srcfname.is_file():
        print(f"'{srcfname}' not found.", file=sys.stderr)
        return None

    return srcfname

def generate_photo_list(photo_list_file, source_dir, remove_prefix=None):
    with open(photo_list_file, "r") as file:
        for line in file.readlines():
            src_fname = process_file_line(line, source_dir, remove_prefix)
            if src_fname is not None:
                yield src_fname

def move_photos(args):
    source_dir = args.source
    destination_dir = args.destination
    remove_prefix = args.remove_prefix
    photo_list_file = args.file
    dry_run = args.dry_run

    if not source_dir.is_dir():
        print(f"Error: Source directory '{source_dir}' does not exist.", file=sys.stderr)
        return

    if not destination_dir.is_dir() and not dry_run:
        destination_dir.mkdir(parents=True)
        print(f"Created destination directory: {destination_dir}", file=sys.stderr)

    for srcfname in generate_photo_list(photo_list_file, source_dir, remove_prefix):
        move_file(srcfname, source_dir, destination_dir, dry_run)