from zipfile import ZipFile
from template.module import validation_error_handler, transform_json_to_dict

def is_data_spec_file_valid(data):
    data_spec_file = transform_json_to_dict(data.read())

    validate_template_name(data_spec_file)

    validate_data_spec_attr(data_spec_file)

    return data_spec_file['templateName']


def validate_template_name(data):
    if 'templateName' not in data and data['templateName']:
       return validation_error_handler({'dataspec_error': 'The dataspec.json file has not templateName attribute and '
                                                 'it must not be empty'})


def validate_data_spec_attr(data):
    sub_attr_bag = []

    for data_spec_attr in data['dataspec']:
        if not data_spec_attr.keys() >= {"field", "description", "required"}:
           return validation_error_handler({'dataspec_error': f'{data_spec_attr} The dataspec array must have the following '
                                                     f'attributes, "field","description","required'})
        sub_attr_bag.append(data_spec_attr['field'])

    for field in sub_attr_bag:
        if not field.startswith('@#') and field.endswith('@#'):
           return validation_error_handler({'dataspec_error': f'The {field} field in dataspec.json '
                                                     f' does not start and end with @#'})


class ValidateZippedFileContent:
    def __init__(self, template_files):

        self.template_files = template_files
        if isinstance(self.template_files, list):
            if 'index.html' not in self.template_files:
                raise validation_error_handler({'file_error': 'Please the template must have an index.html file'})
            if 'css/' not in self.template_files:
                raise validation_error_handler({'file_error': 'Please the template must have a css folder'})
            if 'js/' not in self.template_files:
                raise validation_error_handler({'file_error': 'Please the template must have a js folder'})
            if 'dataspec.json' not in self.template_files:
                raise validation_error_handler({'file_error': 'Please the template must have a dataspec.json file'})

    @staticmethod
    def validate_data_spec_file(template):
        with ZipFile(template) as zipped_file:
            with zipped_file.open('dataspec.json') as data_spec:
                return is_data_spec_file_valid(data_spec)



