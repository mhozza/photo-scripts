
from datetime import timedelta
from os.path import basename
from libs import exif

def register_subcommand(subparsers):
    parser = subparsers.add_parser("shift-time", help="Shift exif DateTimeOriginal by time")
    parser.add_argument("-t", "--time", type=int, required=True, help="time in seconds")
    parser.add_argument("-d", "--dry", action="store_true", help="don't modify anything")
    parser.add_argument("files", nargs="+")
    parser.set_defaults(func=shift_time)

def shift_time(args):
    with exif.ExifTool() as et:
        metadata = et.read_metadata(args.files)
        delta = timedelta(seconds=args.time)
        for data in metadata:
            fname = data[exif.KEY_SOURCE_FILE]
            original_datetime = exif.get_datetime_original(data)
            shifted_datetime = original_datetime + delta
            print(
                f"{basename(fname)} time:{original_datetime.strftime(exif.EXIF_DATETIME_FORMAT)} new_time:{shifted_datetime.strftime(exif.EXIF_DATETIME_FORMAT)}"
            )
            if not args.dry:
                et.set_datetime_original_and_update(fname, shifted_datetime)
