import exiftool
from datetime import datetime

# Constants
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
KEY_DATETIME_ORIGINAL = "EXIF:DateTimeOriginal"
KEY_CREATE_DATE = "EXIF:CreateDate"
KEY_MODIFY_DATE = "EXIF:ModifyDate"
KEY_FILE_MODIFY_DATE = "FileModifyDate"
KEY_SOURCE_FILE = "SourceFile"

class ExifTool:
    def __init__(self):
        self.et = None

    def __enter__(self):
        self.et = exiftool.ExifTool()
        self.et.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.et.__exit__(exc_type, exc_value, traceback)

    def read_metadata(self, files):
        return self.et.get_metadata_batch(files)

    def write_metadata(self, file_path, tags):
        params = [f"-{k}={v}".encode() for k, v in tags.items()]
        args = [file_path.encode()] + params
        self.et.execute(*args)

    def set_datetime_original_and_update(self, file_path, dt):
        dt_str = dt.strftime(EXIF_DATETIME_FORMAT)
        tags = {
            KEY_DATETIME_ORIGINAL: dt_str,
            KEY_CREATE_DATE: dt_str,
            KEY_MODIFY_DATE: dt_str,
            KEY_FILE_MODIFY_DATE: dt_str,
        }
        self.write_metadata(file_path, tags)

# Helper function that don't need a transaction
def get_datetime_original(metadata):
    return datetime.strptime(metadata[KEY_DATETIME_ORIGINAL], EXIF_DATETIME_FORMAT)