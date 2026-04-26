import argparse
from pathlib import Path
import sys

JPEG_EXTS = {'.jpg', '.jpeg'}
RAW_EXTS = {'.cr3'}

def register_subcommand(subparsers):
    parser = subparsers.add_parser("clean-raws", help="Clean up CR3 raw files without a corresponding JPEG")
    parser.add_argument("folder", type=Path, help="folder path to scan")
    parser.add_argument("-r", "--recursive", action="store_true", help="include subfolders")
    parser.set_defaults(func=clean_raws)

def clean_raws(args):
    folder = args.folder
    if not folder.is_dir():
        print(f"Error: {folder} is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    if args.recursive:
        all_files = folder.rglob("*")
    else:
        all_files = folder.glob("*")

    jpg_files = []
    cr3_files = []
    for f in all_files:
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in JPEG_EXTS:
            jpg_files.append(f)
        elif ext in RAW_EXTS:
            cr3_files.append(f)

    # To efficiently match them, store jpegs by their parent directory and stem
    jpg_keys = {(f.parent, f.stem.lower()) for f in jpg_files}

    to_delete = []
    for cr3 in cr3_files:
        if (cr3.parent, cr3.stem.lower()) not in jpg_keys:
            to_delete.append(cr3)

    if not to_delete:
        print("No orphaned raw files found.")
        return

    print(f"Found {len(to_delete)} raw files without a corresponding JPEG:")
    for f in to_delete:
        print(f"  {f}")

    try:
        confirmation = input(f"Do you want to delete these {len(to_delete)} files? [y/N]: ")
        if confirmation.lower() in ('y', 'yes'):
            for f in to_delete:
                try:
                    f.unlink()
                    print(f"Deleted {f}")
                except Exception as e:
                    print(f"Error deleting {f}: {e}", file=sys.stderr)
            print("Cleanup complete.")
        else:
            print("Aborted.")
    except KeyboardInterrupt:
        print("\nAborted.")
