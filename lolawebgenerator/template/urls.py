from django.urls import path
from template.views import templates, template_detaspec, process_template

urlpatterns = [
    path("", templates, name="list.create.templates"),
    path("/<int:id>/dataspec", template_detaspec, name='template.dataspec'),
    path("/<int:id>/process", process_template, name='process.template')

]
