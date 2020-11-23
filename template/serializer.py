from rest_framework import serializers


class TemplateSerializer(serializers.Serializer):
    template_files = serializers.FileField(required=True)
