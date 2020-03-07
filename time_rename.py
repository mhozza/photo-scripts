#!/usr/bin/env python3
import argparse
import os
from datetime import datetime

import exiftool

EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
PATTERN_SUFFIX = "_{index:04}.jpg"

OUTPUT_DATE_FORMAT = "%Y_%m_%d_%H%M%S"


def load_metadata(exif_tool, files):
    return exif_tool.get_metadata_batch(files)


def time_rename(metadata, mode, prefix, start_index=0, reverse=False, dry_run=False):
    def rename(original_datetime, original_fname, index):
        if mode == 0:
            pattern = "%s%s" % (prefix, PATTERN_SUFFIX)
            return pattern.format(index=index + start_index)
        elif mode == 1:
            formatted_date = original_datetime.strftime(OUTPUT_DATE_FORMAT)
            return "{date}-{fname}".format(date=formatted_date, fname=original_fname)
        else:
            raise ValueError("Invalid mode {}".format(mode))

    # check for conflicts
    if mode == 0 and any(os.path.isfile(new_file := rename(None, None, i)) for i in range(0, len(metadata))):
        print("Filename conflict!", new_file)
        return
    # build file list
    file_list = []
    for data in metadata:
        fname = data["SourceFile"]
        original_datetime = datetime.strptime(
            data["EXIF:DateTimeOriginal"], EXIF_DATETIME_FORMAT
        )
        file_list.append((original_datetime, fname))
    # sort
    file_list.sort(reverse=reverse)
    # rename_list
    rename_list = ((f, rename(dt, f, i)) for i, (dt, f) in enumerate(file_list))
    # actual rename
    for old, new in rename_list:
        if dry_run:
            print(f"{old} -> {new}")
        else:
            os.rename(old, new)


def main(args):
    with exiftool.ExifTool() as exif_tool:
        metadata = load_metadata(exif_tool, args.files)
        time_rename(
            metadata,
            mode=args.mode,
            prefix=args.prefix,
            start_index=args.start,
            dry_run=args.dry,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shift exif DateTimeOriginal by time")
    parser.add_argument(
        "-m",
        "--mode",
        type=int,
        default=0,
        help="Mode: 0 - rename to PREFIX_NUMBER, 1 - rename to DATE_FNAME",
    )
    parser.add_argument("-s", "--start", type=int, default=0, help="start index")
    parser.add_argument(
        "-d", "--dry", action="store_true", help="don't modify anything"
    )
    parser.add_argument("-p", "--prefix", default="IMAGE", help="prefix")
    parser.add_argument("files", nargs="+")
    main(parser.parse_args())
