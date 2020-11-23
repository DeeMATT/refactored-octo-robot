from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from template.unzip import UnzipUploadedFile
from template.validatezippedfilecontent import ValidateZippedFileContent
from template.modules import rename_uploaded_file
from template.serializer import TemplateSerializer
from template.models import Template
from template.remotestorage import upload_file_to_bucket, generate_signed_url_from_bucket
from django.core.files.uploadedfile import TemporaryUploadedFile


class TemplateView(ListCreateAPIView):

    parser_classes = [MultiPartParser]

    serializer_class = TemplateSerializer

    def get_queryset(self):
        data = []
        templates = Template.objects.all()

        for template in templates:

            signed_url = generate_signed_url_from_bucket(template.unique_name)

            data.append(
                {'templateName': template.name, 'template_url': signed_url}
            )

        return data

    def post(self, request, *args, **kwargs):

        serialize_data = self.serializer_class(data=request.data)

        if serialize_data.is_valid():
            uploaded_file = request.FILES['template_files']

            template_files = UnzipUploadedFile(uploaded_file).read_zipped_file()

            validated_file = ValidateZippedFileContent(template_files)

            submitted_template_name = validated_file.validate_data_spec_file(uploaded_file)

            modified_file = rename_uploaded_file(uploaded_file)

            temp_upload_file = TemporaryUploadedFile(modified_file.name, 'zip', modified_file.size, 'utf-8')

            upload_file_to_bucket(temp_upload_file.temporary_file_path(), modified_file.name)

            try:

                Template.objects.create(
                    name=submitted_template_name,
                    unique_name=modified_file.name
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