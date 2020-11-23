from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from template.unzip import UnzipUploadedFile
from template.validatezippedfilecontent import ValidateZippedFileContent
from template.modules import rename_uploaded_file
from template.serializer import TemplateSerializer
from template.models import Template


class TemplateView(CreateAPIView):
    serializer_class = TemplateSerializer

    def post(self, request, *args, **kwargs):

        serialize_data = self.serializer_class(data=request.data)

        if serialize_data.is_valid():
            uploaded_file = request.FILES['template_files']

            template_files = UnzipUploadedFile(uploaded_file).read_zipped_file()

            validated_file = ValidateZippedFileContent(template_files)

            submitted_template_name = validated_file.validate_data_spec_file(uploaded_file)

            unique_filename = rename_uploaded_file(uploaded_file)

            try:

                Template.objects.create(
                    name=submitted_template_name,
                    url="https://testaws.com"
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