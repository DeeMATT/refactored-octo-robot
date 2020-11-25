import time
from rest_framework.exceptions import ValidationError
import os
import glob

def rename_uploaded_template(file):
    file.name = f'{time.time()}.zip'
    return file

def delete_downloaded_templates(file_dir):
     files = glob.glob(file_dir)
     os.remove(files[0])

def validation_error_handler(message):
    raise ValidationError(message)