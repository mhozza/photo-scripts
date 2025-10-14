import sys
import os
from pathlib import Path
from photo_scripts.libs import lrcatalogue

ENHANCED_SUFFIX = "-Enhanced-NR.dng"

def find_catalogue_root(paths):
    if not paths:
        return None
    return Path(os.path.commonprefix([str(p) for p in paths]))

def register_subcommand(subparsers):
    parser = subparsers.add_parser("find-unpicked", help="Find unpicked photos in a Lightroom catalog.")
    parser.add_argument("lrcat_path", type=Path, help="Path to the .lrcat file.")
    parser.add_argument("-m", "--directory-mapping", nargs=2, action='append', help="Directory mapping from source to destination, e.g. -m /src /dst")
    parser.add_argument("--catalogue-root", type=Path, help="Path to the catalogue root. If not specified, it will be autodetected as the lowest common ancestor of all photo paths.")
    parser.add_argument("--full-path", action="store_true", default=False, help="Output the full absolute path for the files.")
    parser.set_defaults(func=find_unpicked)

def determine_catalogue_root(catalogue_root_arg, all_photos):
    if catalogue_root_arg:
        return catalogue_root_arg
    else:
        photo_paths = [p.path for p in all_photos]
        return find_catalogue_root(photo_paths)

def find_virtually_picked_raws(all_photos, photos_by_path):
    virtually_picked_raws = set()
    for photo in all_photos:
        if photo.path.suffix.lower() in ['.cr2', '.cr3'] and photo.metadata.picked == lrcatalogue.Picked.UNPICKED:
            enhanced_dng_path = photo.path.with_name(f"{photo.path.stem}{ENHANCED_SUFFIX}")
            if enhanced_dng_path in photos_by_path:
                enhanced_photo = photos_by_path[enhanced_dng_path]
                if enhanced_photo.metadata.picked == lrcatalogue.Picked.PICKED:
                    virtually_picked_raws.add(photo.path)
                    print(f"Warning: {photo.path} is unpicked, but the corresponding enhanced file {enhanced_photo.path} is picked.", file=sys.stderr)
    return virtually_picked_raws

def collect_unpicked_files(all_photos, virtually_picked_raws):
    unpicked_files = []
    for photo in all_photos:
        if photo.metadata.picked == lrcatalogue.Picked.UNPICKED and photo.path not in virtually_picked_raws:
            unpicked_files.append(photo.path)
    return unpicked_files

def print_unpicked_files(unpicked_files, catalogue_root):
    for path in unpicked_files:
        if not catalogue_root:
            print(path)
        else:
            try:
                print(path.relative_to(catalogue_root))
            except ValueError:
                print(f"Warning: {path} is not inside the catalogue root {catalogue_root}. Printing full path.", file=sys.stderr)
                print(path)

def find_unpicked(args):
    directory_mapping = {src: dst for src, dst in args.directory_mapping} if args.directory_mapping else {}
    all_photos = lrcatalogue.get_all_photos(args.lrcat_path, directory_mapping)
    
    full_path = args.full_path
    catalogue_root = None if full_path else determine_catalogue_root(args.catalogue_root, all_photos)
    print(f"Catalogue root: {catalogue_root}, catalogue_root_arg: {args.catalogue_root}", file=sys.stderr)
    
    photos_by_path = {photo.path: photo for photo in all_photos}
    virtually_picked_raws = find_virtually_picked_raws(all_photos, photos_by_path)
    
    unpicked_files = collect_unpicked_files(all_photos, virtually_picked_raws)
    
    print_unpicked_files(unpicked_files, catalogue_root)

    scanned_count = len(all_photos)
    virtually_picked_count = len(virtually_picked_raws)
    print(f"\nScanned {scanned_count} files.", file=sys.stderr)
    print(f"Found {len(unpicked_files)} unpicked files.", file=sys.stderr)
    print(f"Found {virtually_picked_count} unpicked files with a picked enhanced file.", file=sys.stderr)