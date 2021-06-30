from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
import mimetypes
import os
from datetime import datetime
from rest_framework.parsers import MultiPartParser, JSONParser
from .unzip import UnzipUploadedFile
from .validatezippedfilecontent import ValidateZippedFileContent
from .module import (rename_uploaded_template, 
                                delete_downloaded_template, 
                                generateLinearDictionaryOfTemplate,
                                replace_template_placeholders,
                                validate_submitted_data_spec,
                                zip_modified_template,
                                uploadFileToLocal,
                                delete_dir
                                )
from .serializer import TemplateSerializer
from django.shortcuts import HttpResponse
from .models import Template
from .remotestorage import (upload_file_to_bucket,
                                    generate_signed_url_from_bucket,
                                    delete_file_from_bucket,
                                    download_template_from_aws
                                    )
from django.conf import settings


@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser])
def templates(request):
    if request.method == 'POST':
        return post_request_handler(request)
    else:
        return get_request_handler()


def get_request_handler():
        data = []
        templates = Template.objects.all()

        for template in templates:
            name_path = template.unique_name.replace('.', '_')
            folder = f"lola_web_templates/{name_path}"
            template_path = f"{folder}/{template.name}.zip"
            screen_path = f"{folder}/{template.screenshot}"
            signed_url = generate_signed_url_from_bucket(template_path)
            screen_url = generate_signed_url_from_bucket(screen_path)

            # generate url
            bucket_endpoint = settings.BUCKET_ENDPOINT_URL
            bucket_name = settings.BUCKET_NAME

            if not bucket_endpoint.endswith('/'):
                bucket_endpoint = bucket_endpoint + '/'
            
            preview_url = f"{bucket_endpoint}{bucket_name}/{folder}/preview.html"

            data.append(
                {
                    'id': template.id, 
                    'templateName': template.name, 
                    'template_url': signed_url, 
                    'screen_url': screen_url,
                    'preview_url': preview_url
                }
            )

        return Response(data, status=status.HTTP_200_OK)


def post_request_handler(request):

        serialize_data = TemplateSerializer(data=request.data, context={'request': request})

        if serialize_data.is_valid():

            uploaded_template = request.FILES.get('template_files')
            template_screenshot = request.FILES.get('template_screen')

            read_template_files = UnzipUploadedFile(uploaded_template).read_zipped_file()

            validated_template_content = ValidateZippedFileContent(read_template_files)

            submitted_template_name = validated_template_content.validate_data_spec_file(uploaded_template)

            existing_template = is_template_existing(submitted_template_name, template_screenshot.name, uploaded_template)

            if existing_template['status']:

                prepared_file = existing_template['modified_file']

            else:

                prepared_file = rename_uploaded_template(uploaded_template)
            
            mimetype = mimetypes.guess_type(uploaded_template.name)[0]
            name_path = prepared_file.name.replace('.', '_')
            folder = f"lola_web_templates/{name_path}/"
            
            submitted_template_name = submitted_template_name.replace(' ', '_')
            zip_file_path = f"{folder}{submitted_template_name}.zip"
            upload_file_to_bucket(uploaded_template.temporary_file_path(), zip_file_path, content_type=mimetype)

            # screenshot
            mimetype = mimetypes.guess_type(template_screenshot.name)[0]
            screen_file_path = f"{folder}{template_screenshot.name}"
            upload_file_to_bucket(template_screenshot.temporary_file_path(), screen_file_path, content_type=mimetype)

            # extract files
            extracted_files_dir = UnzipUploadedFile(uploaded_template).extract_zipped_file()
            finalOutput =  generateLinearDictionaryOfTemplate(extracted_files_dir)

            # upload
            for filePath in finalOutput:
                mimetype = mimetypes.guess_type(filePath)[0]
                if filePath.endswith('.css'):
                    folderPath = folder + 'css/'
                elif filePath.endswith('.js'):
                    folderPath = folder + 'js/'
                elif filePath.endswith('.html'):
                    folderPath = folder
                else:
                    folderPath = folder + 'assets/'
                
                fileName = os.path.basename(filePath)
                s3FileName = f"{folderPath}{fileName}"
                upload_file_to_bucket(filePath, s3FileName, content_type=mimetype)

            # delete directory to free memory space
            delete_dir(extracted_files_dir)

            try:
                if not existing_template['status']:

                    Template.objects.create(
                        name=submitted_template_name,
                        unique_name=prepared_file.name,
                        screenshot=template_screenshot.name
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


def is_template_existing(name, screen_name, uploaded_template):
    try:
        template = Template.objects.get(name=name)

        uploaded_template.name = template.unique_name
        
        delete_file_from_bucket(template.unique_name)
        if template.screenshot:
            delete_file_from_bucket(template.screenshot)

        # update
        template.screenshot = screen_name
        template.save()


        context = {"status": True, "modified_file": uploaded_template}

        return context

    except Template.DoesNotExist:

        context = {"status": False}

        return context


@api_view(['GET'])
def template_dataspec(request, id):
    try:
        template = Template.objects.get(id=id)

        name_path = template.unique_name.replace('.', '_')
        folder_path = f"lola_web_templates/{name_path}/"
        file_path = f"{folder_path}{template.name}.zip"

        downloaded_template_from_aws_bucket = download_template_from_aws(file_path, folder_path)
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

        # delete directory to free memory space
        delete_dir(extracted_files_dir)

        return file_download(processed_template, template.name)

    except Template.DoesNotExist:
        return Response(f'Template with id {id} was not found', status=status.HTTP_404_NOT_FOUND)


def file_download(template, name):
    file = open(f'{template}.zip', encoding="latin-1", errors='ignore')

    mimetype = mimetypes.guess_type(template)[0]
    response = HttpResponse(file.read(), content_type=mimetype)
    response["Content-Disposition"] = "attachment; filename=%s" % name

    return response

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_processed_template(request, domain):
    serialize_data = TemplateSerializer(data=request.data, context={'request': request})

    if serialize_data.is_valid():
        template = request.FILES.get('template_files')
        template_name = (str(datetime.now().timestamp()) + template.name).replace(" ", "")
        uploadFileToLocal(template, template_name)
        # extract content
        read_template_files = UnzipUploadedFile(template_name).read_zipped_file()

        ValidateZippedFileContent(read_template_files)
        
        extracted_files_dir = UnzipUploadedFile(template).extract_zipped_file()
        finalOutput =  generateLinearDictionaryOfTemplate(extracted_files_dir)

        # upload
        for filePath in finalOutput:
            mimetype = mimetypes.guess_type(filePath)[0]
            folder = f"{domain}_web/"
            if filePath.endswith('.css'):
                folderPath = folder + 'css/'
            elif filePath.endswith('.js'):
                folderPath = folder + 'js/'
            elif filePath.endswith('.html'):
                folderPath = folder
            else:
                folderPath = folder + 'assets/'
            
            fileName = os.path.basename(filePath)
            s3FileName = f"{folderPath}{fileName}"
            upload_file_to_bucket(filePath, s3FileName, content_type=mimetype)
    
        # delete directory to free memory space
        delete_dir(extracted_files_dir)

        # generate url
        bucket_endpoint = settings.BUCKET_ENDPOINT_URL
        bucket_name = settings.BUCKET_NAME

        if not bucket_endpoint.endswith('/'):
            bucket_endpoint = bucket_endpoint + '/'
        
        template_url = f"{bucket_endpoint}{bucket_name}/{folder}"
        data = {
            "domain": domain,
            "template_url": template_url
        }
        
        return Response(data, status=status.HTTP_200_OK)
