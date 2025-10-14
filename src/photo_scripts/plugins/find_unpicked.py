import sys
from pathlib import Path
from photo_scripts.libs import lrcatalogue

ENHANCED_SUFFIX = "-Enhanced-NR.dng"

def register_subcommand(subparsers):
    parser = subparsers.add_parser("find-unpicked", help="Find unpicked photos in a Lightroom catalog.")
    parser.add_argument("lrcat_path", type=Path, help="Path to the .lrcat file.")
    parser.add_argument("-m", "--directory-mapping", nargs=2, action='append', help="Directory mapping from source to destination, e.g. -m /src /dst")
    parser.set_defaults(func=find_unpicked)

def find_unpicked(args):
    directory_mapping = {src: dst for src, dst in args.directory_mapping} if args.directory_mapping else {}
    all_photos = lrcatalogue.get_all_photos(args.lrcat_path, directory_mapping)
    
    photos_by_path = {photo.path: photo for photo in all_photos}
    virtually_picked_raws = set()

    for photo in all_photos:
        if photo.path.suffix.lower() in ['.cr2', '.cr3'] and photo.metadata.picked == lrcatalogue.Picked.UNPICKED:
            enhanced_dng_path = photo.path.with_name(f"{photo.path.stem}{ENHANCED_SUFFIX}")
            if enhanced_dng_path in photos_by_path:
                enhanced_photo = photos_by_path[enhanced_dng_path]
                if enhanced_photo.metadata.picked == lrcatalogue.Picked.PICKED:
                    virtually_picked_raws.add(photo.path)
                    print(f"Warning: {photo.path} is unpicked, but the corresponding enhanced file {enhanced_photo.path} is picked.", file=sys.stderr)

    unpicked_files = []
    for photo in all_photos:
        if photo.metadata.picked == lrcatalogue.Picked.UNPICKED and photo.path not in virtually_picked_raws:
            unpicked_files.append(photo.path)

    for path in unpicked_files:
        print(path)

    scanned_count = len(all_photos)
    print(f"\nScanned {scanned_count} files.", file=sys.stderr)
    print(f"Found {len(unpicked_files)} unpicked files.", file=sys.stderr)