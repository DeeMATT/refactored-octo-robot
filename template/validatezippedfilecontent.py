from rest_framework.exceptions import ValidationError
from zipfile import ZipFile
import json


def is_data_spec_file_valid(data):
    data_spec_file = json.loads(data.read())

    validate_template_name(data_spec_file)

    validate_data_spec_attr(data_spec_file)

    return data_spec_file['templateName']


def validate_template_name(data):
    if 'templateName' not in data and data['templateName']:
        raise ValidationError({'dataspec_error': 'The dataspec.json file has not templateName attribute and '
                                                 'it must not be empty'})


def validate_data_spec_attr(data):
    sub_attr_bag = []

    for data_spec_attr in data['dataspec']:
        if not data_spec_attr.keys() >= {"field", "description", "required", 'required'}:
            raise ValidationError({'dataspec_error': f'{data_spec_attr} The dataspec array must have the following '
                                                     f'attributes, "field","description","required'})
        sub_attr_bag.append(data_spec_attr['field'])

    for valid_field_value in sub_attr_bag:
        if not valid_field_value.startswith('@#') and valid_field_value.endswith('@#'):
            raise ValidationError({'dataspec_error': f'The {valid_field_value} field in dataspec.json '
                                                     f' does not start and end with @#'})


class ValidateZippedFileContent:
    def __init__(self, template_files):
        self.template_files = template_files
        if isinstance(self.template_files, list):
            if 'index.html' not in self.template_files:
                raise ValidationError({'file_error': 'Please the template must have an index.html file'})
            if 'css/' not in self.template_files:
                raise ValidationError({'file_error': 'Please the template must have a css folder'})
            if 'js/' not in self.template_files:
                raise ValidationError({'file_error': 'Please the template must have a js folder'})
            if 'dataspec.json' not in self.template_files:
                raise ValidationError({'file_error': 'Please the template must have a dataspec.json file'})

    @staticmethod
    def validate_data_spec_file(template):
        with ZipFile(template) as zipped_file:
            with zipped_file.open('dataspec.json') as data_spec:
                return is_data_spec_file_valid(data_spec)



