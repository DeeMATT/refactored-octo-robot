from django.urls import path
from template.views import templates, template_dataspec, process_template, upload_processed_template

urlpatterns = [
    path("", templates, name="list.create.templates"),
    path("/<int:id>/dataspec", template_dataspec, name='template.dataspec'),
    path("/<int:id>/process", process_template, name='process.template'),
    path("/upload-template", upload_processed_template)
]
