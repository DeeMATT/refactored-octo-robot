from zipfile import ZipFile, is_zipfile
from rest_framework.exceptions import ValidationError
from template.module import validation_error_handler
import json

class UnzipUploadedFile:
    zipped_file = ''

    def __init__(self, uploaded_file):
        self.file = uploaded_file
        self.validate_file_is_zip()

    def validate_file_is_zip(self):
        if is_zipfile(self.file):
            return self
        else:
            return  validation_error_handler({'file_error': 'Template files must be in a zipped format'})

    def read_zipped_file(self):
        with ZipFile(self.file, 'r') as zipped_file:
            self.zipped_file = zipped_file
            return zipped_file.namelist()

    def read_dataspec_file(self):
         with ZipFile(self.file) as zipped_file:
            with zipped_file.open('dataspec.json') as data_spec:
                return json.loads(data_spec.read())

