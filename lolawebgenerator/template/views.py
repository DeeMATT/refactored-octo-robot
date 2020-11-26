from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
import mimetypes
from rest_framework.parsers import MultiPartParser, JSONParser
from template.unzip import UnzipUploadedFile
from template.validatezippedfilecontent import ValidateZippedFileContent
from template.module import (rename_uploaded_template, 
                                delete_downloaded_template, 
                                generateLinearDictionaryOfTemplate,
                                replace_template_placeholders,
                                validate_submitted_data_spec,
                                zip_modified_template
                                )
from template.serializer import TemplateSerializer
from django.shortcuts import HttpResponse
from template.models import Template
from template.remotestorage import (upload_file_to_bucket,
                                    generate_signed_url_from_bucket,
                                    delete_file_from_bucket,
                                    download_template_from_aws
                                    )

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser])
def templates(request):
    if request.method == 'POST':
        return  post_request_handler(request)
    else:
         return get_request_handler()


def get_request_handler():
        data = []
        templates = Template.objects.all()

        for template in templates:

            signed_url = generate_signed_url_from_bucket(template.unique_name)

            data.append(
                {'id':template.id, 'templateName': template.name, 'template_url': signed_url}
            )

        return Response(data,status=status.HTTP_200_OK)


def post_request_handler(request):

        serialize_data = TemplateSerializer(data=request.data, context={'request':request})

        if serialize_data.is_valid():

            uploaded_template = request.FILES['template_files']

            read_template_files = UnzipUploadedFile(uploaded_template).read_zipped_file()

            validated_template_content = ValidateZippedFileContent(read_template_files)

            submitted_template_name = validated_template_content.validate_data_spec_file(uploaded_template)

            existing_template = is_template_existing(submitted_template_name,uploaded_template)

            if existing_template['status']:

                prepared_file = existing_template['modified_file']

            else:

                prepared_file = rename_uploaded_template(uploaded_template)

            upload_file_to_bucket(uploaded_template.temporary_file_path(), prepared_file.name)

            try:
                if not existing_template['status']:

                    Template.objects.create(
                        name=submitted_template_name,
                        unique_name=prepared_file.name
                    )

                context = {
                    'status': 'success',
                    'message': 'Template saved',
                    'code': 200
                }

                return Response(context, status=status.HTTP_200_OK)

            except Exception as e:

                return Response({e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response(serialize_data.errors, status=status.HTTP_400_BAD_REQUEST)


def is_template_existing(name, uploaded_template):
    try:
        template = Template.objects.get(name=name)

        uploaded_template.name = template.unique_name

        delete_file_from_bucket(template.unique_name)

        context = {"status":True, "modified_file":uploaded_template}

        return context

    except Template.DoesNotExist:

        context = {"status":False}

        return context


@api_view(['GET'])
def template_detaspec(request, id):
    try:
        template = Template.objects.get(id=id)

        downloaded_template_from_aws_bucket = download_template_from_aws(template.unique_name)

        read_dataspec_content = UnzipUploadedFile(downloaded_template_from_aws_bucket).read_dataspec_file()

        delete_downloaded_template(downloaded_template_from_aws_bucket)

        return Response(read_dataspec_content['dataspec'], status=status.HTTP_200_OK)

    except Template.DoesNotExist:
        return Response(f'Template with id {id} was not found', status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@parser_classes([JSONParser])
def process_template(request, id):

    valid_submitted_data_spec = validate_submitted_data_spec(request)

    try:
        template = Template.objects.get(id=id)

        downloaded_template_from_aws_bucket = download_template_from_aws(template.unique_name)

        extracted_files_dir = UnzipUploadedFile(downloaded_template_from_aws_bucket).extract_zipped_file()

        finalOutput =  generateLinearDictionaryOfTemplate(extracted_files_dir)

        replace_template_placeholders(finalOutput, valid_submitted_data_spec)

        processed_template = zip_modified_template(template.name, extracted_files_dir)

        return file_download(processed_template, template.name)

    except Template.DoesNotExist:
        return Response(f'Template with id {id} was not found', status=status.HTTP_404_NOT_FOUND)

def file_download(template, name):
    file = open(f'{template}.zip', encoding="latin-1", errors='ignore')

    mimetype = mimetypes.guess_type(template)

    response = HttpResponse(file.read(), content_type =mimetype)

    response["Content-Disposition"]= "attachment; filename=%s" % name

    return response