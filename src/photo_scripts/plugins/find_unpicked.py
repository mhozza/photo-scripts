"""
This plugin finds unpicked photos in a Lightroom catalog.
It can also check for the existence of picked files and remap file paths.
"""
import sys
import os
from pathlib import Path
from photo_scripts.libs import lrcatalogue

ENHANCED_SUFFIX = "-Enhanced-NR.dng"

def find_catalogue_root(paths):
    """Finds the lowest common ancestor of a list of paths."""
    if not paths:
        return None
    return Path(os.path.commonpath([str(p) for p in paths]))

def register_subcommand(subparsers):
    """Registers the 'find-unpicked' subcommand."""
    parser = subparsers.add_parser("find-unpicked", help="Find unpicked photos in a Lightroom catalog.")
    parser.add_argument("lrcat_path", type=Path, help="Path to the .lrcat file.")
    parser.add_argument("--catalogue-root", type=Path, help="Path to the catalogue root. If not specified, it will be autodetected as the lowest common ancestor of all photo paths.")
    parser.add_argument("--file-root", type=Path, help="New root path for the files.")
    parser.add_argument("--check-files", action="store_true", default=False, help="Check for the existence of picked files.")
    parser.add_argument("--skip-outside-root", action="store_true", default=False, help="Skip files outside the specified root path.")
    parser.add_argument("--full-path", action="store_true", default=False, help="Output the full absolute path for the files.")
    parser.set_defaults(func=find_unpicked)

def determine_catalogue_root(catalogue_root_arg, all_photos):
    """Determines the catalogue root path."""
    if catalogue_root_arg:
        return catalogue_root_arg
    else:
        photo_paths = [p.path for p in all_photos]
        return find_catalogue_root(photo_paths)

def remap_path(path, catalogue_root, file_root_path):
    """Remaps a path from the catalogue root to a new file root."""
    if not file_root_path or not catalogue_root:
        return path
    try:
        return file_root_path / path.relative_to(catalogue_root)
    except ValueError:
        return None

def check_picked_files(photos, catalogue_root, file_root_path):
    """Checks for the existence of picked files."""
    if not file_root_path:
        print("Error: --check-files requires --file-root-path to be specified.", file=sys.stderr)
        return 0, 0

    non_existing_count = 0
    non_existing_original_count = 0

    for photo in photos:
        is_picked = any(vc.metadata.picked == lrcatalogue.Picked.PICKED for vc in photo.virtual_copies)
        if is_picked:
            remapped_path = remap_path(photo.path, catalogue_root, file_root_path)
            if remapped_path and not remapped_path.exists():
                non_existing_count += 1
                # Check for the enhanced version of the file
                enhanced_path = remapped_path.with_name(f"{remapped_path.stem}{ENHANCED_SUFFIX}")
                if enhanced_path.exists():
                    non_existing_original_count += 1
                    print(f"Warning: Picked file {remapped_path} does not exist, but enhanced file {enhanced_path} exists.", file=sys.stderr)
                else:
                    print(f"Warning: Picked file {remapped_path} does not exist.", file=sys.stderr)
    
    return non_existing_count, non_existing_original_count

def find_virtually_picked_raws(all_photos, photos_by_path):
    """Finds RAW files that are unpicked but have a picked enhanced version."""
    virtually_picked_raws = set()
    for photo in all_photos:
        is_unpicked = all(vc.metadata.picked == lrcatalogue.Picked.UNPICKED for vc in photo.virtual_copies)
        # Check for unpicked RAW files
        if photo.path.suffix.lower() in ['.cr2', '.cr3'] and is_unpicked:
            # Check if an enhanced version exists
            enhanced_dng_path = photo.path.with_name(f"{photo.path.stem}{ENHANCED_SUFFIX}")
            if enhanced_dng_path in photos_by_path:
                enhanced_photo = photos_by_path[enhanced_dng_path]
                # Check if the enhanced version is picked
                if any(vc.metadata.picked == lrcatalogue.Picked.PICKED for vc in enhanced_photo.virtual_copies):
                    virtually_picked_raws.add(photo.path)
                    print(f"Warning: {photo.path} is unpicked, but at least one virtual copy of the corresponding enhanced file {enhanced_photo.path} is picked.", file=sys.stderr)
    return virtually_picked_raws

def collect_unpicked_files(all_photos, virtually_picked_raws):
    """Collects all unpicked files, excluding virtually picked raws."""
    unpicked_files = []
    for photo in all_photos:
        is_unpicked = all(vc.metadata.picked == lrcatalogue.Picked.UNPICKED for vc in photo.virtual_copies)
        if is_unpicked and photo.path not in virtually_picked_raws:
            unpicked_files.append(photo.path)
    return unpicked_files

def filter_photos_by_catalogue_root(all_photos, catalogue_root, skip_outside_root):
    """Filters photos to only include those inside the catalogue root."""
    if not catalogue_root:
        return all_photos

    filtered_photos = []
    for photo in all_photos:
        try:
            photo.path.relative_to(catalogue_root)
            filtered_photos.append(photo)
        except ValueError:
            if not skip_outside_root:
                print(f"Warning: {photo.path} is not inside the catalogue root {catalogue_root}. Skipping.", file=sys.stderr)
    
    return filtered_photos

def print_unpicked_files(unpicked_files, catalogue_root, file_root_path, full_path):
    """Prints the list of unpicked files."""
    for path in unpicked_files:        
        if full_path or not catalogue_root:
            if file_root_path:
                remapped_path = remap_path(path, catalogue_root, file_root_path)
                if remapped_path:
                    print(remapped_path)
            else:
                print(path)
        else:
            print(path.relative_to(catalogue_root))

def find_unpicked(args):
    """Main function for the 'find-unpicked' subcommand."""
    # Get all photos from the Lightroom catalog
    all_photos_from_db = lrcatalogue.get_all_photos(args.lrcat_path)
    scanned_count = len(all_photos_from_db)

    full_path = args.full_path
    # Determine the catalogue root path
    catalogue_root = determine_catalogue_root(args.catalogue_root, all_photos_from_db)

    # Filter photos to only include those inside the catalogue root
    photos_in_root = filter_photos_by_catalogue_root(all_photos_from_db, catalogue_root, args.skip_outside_root)
    filtered_count = scanned_count - len(photos_in_root)

    # Check for the existence of picked files if requested
    non_existing_count = 0
    non_existing_original_count = 0
    if args.check_files:
        non_existing_count, non_existing_original_count = check_picked_files(photos_in_root, catalogue_root, args.file_root)

    # Create a dictionary of photos by path for quick lookup
    photos_by_path = {photo.path: photo for photo in photos_in_root}
    # Find RAW files that are unpicked but have a picked enhanced version
    virtually_picked_raws = find_virtually_picked_raws(photos_in_root, photos_by_path)
    
    # Collect all unpicked files
    unpicked_files = collect_unpicked_files(photos_in_root, virtually_picked_raws)
    
    # Print the list of unpicked files
    print_unpicked_files(unpicked_files, catalogue_root, args.file_root, full_path)

    virtually_picked_count = len(virtually_picked_raws)
    print(f"\nScanned {scanned_count} files.", file=sys.stderr)
    print(f"Filtered out {filtered_count} files not in catalogue root.", file=sys.stderr)
    print(f"Found {len(unpicked_files)} unpicked files.", file=sys.stderr)
    print(f"Found {virtually_picked_count} unpicked files with a picked enhanced file.", file=sys.stderr)
    if args.check_files:
        print(f"Found {non_existing_count} non-existing picked files.", file=sys.stderr)
        print(f"Found {non_existing_original_count} non-existing original files with an existing enhanced file.", file=sys.stderr)
