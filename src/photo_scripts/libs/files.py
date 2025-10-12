import shutil
from pathlib import Path
import sys

def move_file(src_file: Path, src_dir: Path, dest_dir: Path, dry_run: bool = False, overwrite: bool = False):
    """
    Moves a file from src_file to a destination directory, maintaining the relative directory structure from src_dir.
    """
    try:
        relative_path = src_file.relative_to(src_dir)
        dest_file = dest_dir / relative_path

        if not overwrite and dest_file.exists():
            print(f"'{dest_file}' already exists. Skipping.", file=sys.stderr)
            return False

        print(f"Moving: {src_file} to {dest_file}")
        if not dry_run:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_file), str(dest_file))
        return True
    except Exception as e:
        print(f"Error moving {src_file}: {e}", file=sys.stderr)
        return False
