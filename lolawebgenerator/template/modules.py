import time


def rename_uploaded_file(file):
    file.name = f'{time.time()}.zip'
    return file
