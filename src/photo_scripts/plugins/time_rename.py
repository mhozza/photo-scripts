
import os
from libs import exif

PATTERN_SUFFIX = "_{index:04}.jpg"
OUTPUT_DATE_FORMAT = "%Y_%m_%d_%H%M%S"

def register_subcommand(subparsers):
    parser = subparsers.add_parser("time-rename", help="Rename files based on EXIF time")
    parser.add_argument(
        "-m",
        "--mode",
        type=int,
        default=0,
        help="Mode: 0 - rename to PREFIX_NUMBER, 1 - rename to DATE_FNAME",
    )
    parser.add_argument("-s", "--start", type=int, default=0, help="start index")
    parser.add_argument("-d", "--dry", action="store_true", help="don't modify anything")
    parser.add_argument("-p", "--prefix", default="IMAGE", help="prefix")
    parser.add_argument("files", nargs="+")
    parser.set_defaults(func=time_rename)

def time_rename(args):
    with exif.ExifTool() as et:
        metadata = et.read_metadata(args.files)

        def rename(original_datetime, original_fname, index):
            if args.mode == 0:
                pattern = f"{args.prefix}{PATTERN_SUFFIX}"
                return pattern.format(index=index + args.start)
            elif args.mode == 1:
                formatted_date = original_datetime.strftime(OUTPUT_DATE_FORMAT)
                return f"{formatted_date}-{original_fname}"
            else:
                raise ValueError(f"Invalid mode {args.mode}")

        # check for conflicts
        if args.mode == 0 and any(
            os.path.isfile(new_file := rename(None, None, i)) for i in range(0, len(metadata))
        ):
            print("Filename conflict!", new_file)
            return

        # build file list
        file_list = []
        for data in metadata:
            fname = data[exif.KEY_SOURCE_FILE]
            original_datetime = exif.get_datetime_original(data)
            file_list.append((original_datetime, fname))

        # sort
        file_list.sort()

        # rename_list
        rename_list = ((f, rename(dt, f, i)) for i, (dt, f) in enumerate(file_list))

        # actual rename
        for old, new in rename_list:
            if args.dry:
                print(f"{old} -> {new}")
            else:
                os.rename(old, new)
