import argparse
import os
import shutil
import sys
from pathlib import Path


nonexiting_files = []

def process_file_line(fname, src, dst, remove_prefix = None, owerwrite=False):
    fname = Path(fname.strip())

    if remove_prefix is not None and fname.is_relative_to(remove_prefix):
        fname = fname.relative_to(remove_prefix)

    if not fname.is_relative_to(src):
        srcfname = src / fname
        dstfname = dst / fname    
    else:
        srcfname = fname
        dstfname = dst / fname.relative_to(src)
        
    if not srcfname.is_file():
        print(f"'{srcfname}' not found.", file=sys.stderr)
        return None
    
    if not owerwrite and dstfname.is_file():
        print(f"'{dstfname}' already exists.", file=sys.stderr)
        return None

    return srcfname, dstfname


def generate_photo_list(photo_list_file, source_dir, destination_dir, remove_prefix = None, owerwrite=False):
    with open(photo_list_file, "r") as file:
        for line in file.readlines():            
            src_dst = process_file_line(line, source_dir, destination_dir, remove_prefix, owerwrite)
            if src_dst is not None:
                yield src_dst
   

def main():
    """
    Main function to handle photo moving based on flags.
    """
    parser = argparse.ArgumentParser(description="Move photos based on criteria.")
    parser.add_argument("-s", "--source", required=True, help="Source directory of photos.")
    parser.add_argument("-d", "--destination", required=True, help="Destination directory to move photos to.")
    parser.add_argument("-r", "--remove_prefix", required=False, help="Remove prefix from files")
    parser.add_argument("-f", "--file", required=True, help="File with a list of photos to move")
    parser.add_argument("--dry_run", action="store_true", required=False, help="File with a list of photos to move")

    args = parser.parse_args()

    source_dir = Path(args.source)
    destination_dir = Path(args.destination)
    remove_prefix = Path(args.remove_prefix) if args.remove_prefix is not None else None
    photo_list_file = args.file
    dry_run = args.dry_run

    if not source_dir.is_dir():
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    if not destination_dir.is_dir():        
        destination_dir.mkdir(parents=True)
        print(f"Created destination directory: {destination_dir}", file=sys.stderr)
         
    for srcfname, dstfname in generate_photo_list(photo_list_file, source_dir, destination_dir, remove_prefix):
        try:
            if not dry_run:
                if not dstfname.parent.is_dir():
                    dstfname.parent.mkdir(parents=True)
                shutil.move(str(srcfname), str(dstfname))
            print(f"Moved: {srcfname} to {dstfname}")
        except Exception as e:
            print(f"Error moving {srcfname} to {dstfname}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
