
from pathlib import Path
from photo_scripts.libs import lrcatalogue

def register_subcommand(subparsers):
    parser = subparsers.add_parser("find-unpicked", help="Find unpicked photos in a Lightroom catalog.")
    parser.add_argument("lrcat_path", type=Path, help="Path to the .lrcat file.")
    parser.add_argument("-m", "--directory-mapping", nargs=2, action='append', help="Directory mapping from source to destination, e.g. -m /src /dst")
    parser.set_defaults(func=find_unpicked)

def find_unpicked(args):
    directory_mapping = {src: dst for src, dst in args.directory_mapping} if args.directory_mapping else {}
    unpicked_photos = lrcatalogue.get_unpicked_photos(args.lrcat_path, directory_mapping)
    for photo in unpicked_photos:
        print(photo.path)
