
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from libs import exif

class TestExif(unittest.TestCase):

    def test_get_datetime_original(self):
        metadata = {exif.KEY_DATETIME_ORIGINAL: "2023:10:08 10:00:00"}
        dt = exif.get_datetime_original(metadata)
        self.assertEqual(dt, datetime(2023, 10, 8, 10, 0, 0))

@patch('exiftool.ExifTool')
class TestExifTool(unittest.TestCase):

    def test_read_metadata(self, mock_exiftool):
        mock_et_instance = MagicMock()
        mock_exiftool.return_value = mock_et_instance
        
        with exif.ExifTool() as et:
            et.read_metadata(['a.jpg', 'b.jpg'])
        
        mock_et_instance.__enter__.return_value.get_metadata_batch.assert_called_with(['a.jpg', 'b.jpg'])

    def test_write_metadata(self, mock_exiftool):
        mock_et_instance = MagicMock()
        mock_exiftool.return_value = mock_et_instance
        
        tags = {"EXIF:Artist": "test"}

        with exif.ExifTool() as et:
            et.write_metadata('a.jpg', tags)

        mock_et_instance.__enter__.return_value.execute.assert_called_with(b'a.jpg', b'-EXIF:Artist=test')

    def test_set_datetime_original_and_update(self, mock_exiftool):
        mock_et_instance = MagicMock()
        mock_exiftool.return_value = mock_et_instance
        
        dt = datetime(2023, 10, 8, 10, 0, 0)
        dt_str = dt.strftime(exif.EXIF_DATETIME_FORMAT)

        with exif.ExifTool() as et:
            et.set_datetime_original_and_update('a.jpg', dt)

        expected_tags = {
            exif.KEY_DATETIME_ORIGINAL: dt_str,
            exif.KEY_CREATE_DATE: dt_str,
            exif.KEY_MODIFY_DATE: dt_str,
            exif.KEY_FILE_MODIFY_DATE: dt_str,
        }
        
        # Build expected params
        params = [f"-{k}={v}".encode() for k, v in expected_tags.items()]
        args = [b'a.jpg'] + params
        
        mock_et_instance.__enter__.return_value.execute.assert_called_with(*args)

if __name__ == '__main__':
    unittest.main()
