#!/usr/bin/python3
import exiftool
import argparse
from datetime import datetime, timedelta
from os.path import basename

EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"


def load_metadata(exif_tool, files):
    return exif_tool.get_metadata_batch(files)


def shift_time(exif_tool, metadata, time, dry_run=False):
    delta = timedelta(seconds=time)
    for data in metadata:
        fname = data["SourceFile"]
        original_datetime = datetime.strptime(data["EXIF:DateTimeOriginal"], EXIF_DATETIME_FORMAT)
        shifted_datetime = original_datetime + delta
        print("{} time:{} new_time:{}".format(
            basename(fname),
            datetime.strftime(original_datetime, EXIF_DATETIME_FORMAT),
            datetime.strftime(shifted_datetime, EXIF_DATETIME_FORMAT),
        ))
        if not dry_run:
            exif_tool.execute(
                fname.encode(),
                "-EXIF:DateTimeOriginal={}".format(
                    datetime.strftime(shifted_datetime, EXIF_DATETIME_FORMAT)
                ).encode(),
                "-EXIF:CreateDate={}".format(
                    datetime.strftime(shifted_datetime, EXIF_DATETIME_FORMAT)
                ).encode(),
                "-EXIF:ModifyDate={}".format(
                    datetime.strftime(shifted_datetime, EXIF_DATETIME_FORMAT)
                ).encode(),
                "-FileModifyDate={}".format(
                    datetime.strftime(shifted_datetime, EXIF_DATETIME_FORMAT)
                ).encode(),
            )


def main(args):
    with exiftool.ExifTool() as exif_tool:
        metadata = load_metadata(exif_tool, args.files)
        shift_time(exif_tool, metadata, args.time, dry_run=args.dry)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shift exif DateTimeOriginal by time')
    parser.add_argument('-t', '--time', type=int, required=True, help='time in seconds')
    parser.add_argument('-d', '--dry', action='store_true', help='don\'t modify anything')
    parser.add_argument('files', nargs='+')
    main(parser.parse_args())
