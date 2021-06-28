import time
from rest_framework.exceptions import ValidationError
import os
import json
import re
import shutil
from django.conf import settings


def transform_json_to_dict(file):
    return json.loads(file)

def rename_uploaded_template(file):
    file.name = f'{time.time()}.zip'
    return file

def delete_downloaded_template(file:list):
    os.remove(file)

def validation_error_handler(message):
    raise ValidationError(message)

def validate_submitted_data_spec(request):
    json_payload_to_dict = transform_json_to_dict(request.body)

    if 'dataspec' not in json_payload_to_dict:
        message =  {
            "error" : "The dataspec json payload should be in the format below",
            "format": {
                "dataspec": {
                    "@#Home#@": "Homepage Navbar",
                    "@#Here#@": "Here Navbar",
                    "@#Logo#@": "Our cool logo"
                    }
                }
            }
        return validation_error_handler(message)
    else:
        return json_payload_to_dict

def generateLinearDictionaryOfTemplate(providedPath):
    from os import listdir
    from os.path import isfile, join, abspath
    if not providedPath.endswith("/"):
        providedPath = f"{providedPath}/"
    directoryContents = listdir(providedPath)
    filesToIgnore = ['dataspec.json']
    filesInThisDirectory = [
        f for f in directoryContents if isfile(join(providedPath, f))]
    foldersInThisDirectory = [
        f for f in directoryContents if not isfile(join(providedPath, f))]
    result = []
    for fileEntry in filesInThisDirectory:
        if not fileEntry in filesToIgnore:
            result.append(abspath(f"{providedPath}{fileEntry}"))
    for folderEntry in foldersInThisDirectory:
        result.extend(generateLinearDictionaryOfTemplate(
            f"{providedPath}{folderEntry}"))
    return result

def replace_template_placeholders(files, valid_dataspec):
    for file in files:
        open_file = open(file,'r', encoding="latin-1", errors='ignore')
        file_content_to_string = open_file.read()
        for k, v in valid_dataspec['dataspec'].items():
            pattern = re.compile(k, re.IGNORECASE)
            file_content_to_string = pattern.sub(v, file_content_to_string)
        open_file.close()
        write_to_file(file_content_to_string, file)

def write_to_file(file_content_to_string, file):
        new_file = open(file,'w', encoding="latin-1", errors='ignore')
        new_file.write(file_content_to_string)
        new_file.close()

def zip_modified_template(filename, extracted_template_dir):

        '''
        zip modified template
        '''
        if not os.path.isdir(settings.PROCESSED_TEMPLATES_DIR):

            os.mkdir(settings.PROCESSED_TEMPLATES_DIR)

        processed_template_path = f'{settings.PROCESSED_TEMPLATES_DIR}{filename}{time.time()}'

        shutil.make_archive(processed_template_path, 'zip', extracted_template_dir)

        '''
        delete extracted file dir
        '''
        shutil.rmtree(extracted_template_dir)

        return processed_template_path

def uploadFileToLocal(file, localPath):
    with open(localPath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return True

def delete_dir(directory):
    try:
        shutil.rmtree(directory)
    except OSError as e:
        print("Error: %s : %s" % (directory, e.strerror))
