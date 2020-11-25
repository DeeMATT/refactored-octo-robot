import time
from rest_framework.exceptions import ValidationError

def rename_uploaded_template(file):
    file.name = f'{time.time()}.zip'
    return file

def validation_error_handler(message):
    raise ValidationError(message)