from zipfile import ZipFile, is_zipfile
from rest_framework.exceptions import ValidationError


class UnzipUploadedFile:
    zipped_file = ''

    def __init__(self, uploaded_file):
        self.file = uploaded_file
        self.validate_file_is_zip()

    def validate_file_is_zip(self):
        if is_zipfile(self.file):
            return self
        else:
            raise ValidationError({'file_error': 'Template files must be in a zipped format'})

    def read_zipped_file(self):
        with ZipFile(self.file, 'r') as zipped_file:
            self.zipped_file = zipped_file
            return zipped_file.namelist()

