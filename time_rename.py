#!/usr/bin/env python3
import argparse
import os
from datetime import datetime

import exiftool

EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
PATTERN_SUFFIX = "_{index:04}.jpg"


def load_metadata(exif_tool, files):
    return exif_tool.get_metadata_batch(files)


def time_rename(metadata, pattern, start_index=0, reverse=False, dry_run=False):
    def fn(i):
        return pattern.format(index=i + start_index)
    # check for conflicts
    if any(os.path.isfile(fn(i)) for i in range(0, len(metadata))):
        print("Filename conflict!", pattern)
        return
    # build file list
    file_list = []
    for data in metadata:
        fname = data["SourceFile"]
        original_datetime = datetime.strptime(data["EXIF:DateTimeOriginal"], EXIF_DATETIME_FORMAT)
        file_list.append((original_datetime, fname))
    # sort
    file_list.sort(reverse=reverse)
    # rename_list
    rename_list = ((f, fn(i)) for i, (_, f) in enumerate(file_list))
    # actual rename
    for old, new in rename_list:
        if dry_run:
            print(old, new)
        else:
            os.rename(old, new)


def main(args):
    with exiftool.ExifTool() as exif_tool:
        metadata = load_metadata(exif_tool, args.files)
        time_rename(metadata, pattern='%s%s' % (args.prefix, PATTERN_SUFFIX), start_index=args.start, dry_run=args.dry)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shift exif DateTimeOriginal by time')
    parser.add_argument('-s', '--start', type=int, default=0, help='start index')
    parser.add_argument('-d', '--dry', action='store_true', help='don\'t modify anything')
    parser.add_argument('-p', '--prefix', default='IMAGE', help='prefix')
    parser.add_argument('files', nargs='+')
    main(parser.parse_args())
