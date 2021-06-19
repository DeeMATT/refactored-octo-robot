from rest_framework import serializers


class TemplateSerializer(serializers.Serializer):
    template_files = serializers.FileField(required=True, write_only=True)
    template_screen = serializers.FileField(required=False, write_only=True)
    templateName = serializers.CharField(read_only=True)
    template_url = serializers.CharField(read_only=True)

