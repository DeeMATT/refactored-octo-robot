from rest_framework.generics import ListCreateAPIView
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from template.unzip import UnzipUploadedFile
from template.validatezippedfilecontent import ValidateZippedFileContent
from template.modules import rename_uploaded_file
from template.serializer import TemplateSerializer
from template.models import Template
from template.remotestorage import upload_file_to_bucket, generate_signed_url_from_bucket, delete_file_from_bucket

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
                {'templateName': template.name, 'template_url': signed_url}
            )

        return Response(data,status=status.HTTP_200_OK)


def post_request_handler(request):

        serialize_data = TemplateSerializer(data=request.data, context={'request':request})

        if serialize_data.is_valid():

            uploaded_file = request.FILES['template_files']

            template_files = UnzipUploadedFile(uploaded_file).read_zipped_file()

            validated_file = ValidateZippedFileContent(template_files)

            submitted_template_name = validated_file.validate_data_spec_file(uploaded_file)

            template_exists = is_template_existing(submitted_template_name,uploaded_file)

            if template_exists['status']:

                prepared_file = template_exists['mod_file']

            else:

                prepared_file = rename_uploaded_file(uploaded_file)

            upload_file_to_bucket(uploaded_file.temporary_file_path(), prepared_file.name)

            try:
                if not template_exists['status']:

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


def is_template_existing(name, uploaded_file):
    try:
        template = Template.objects.get(name=name)

        uploaded_file.name = template.unique_name

        delete_file_from_bucket(template.unique_name)

        context = {"status":True, "mod_file":uploaded_file}

        return context

    except Template.DoesNotExist:

        context = {"status":False}

        return context