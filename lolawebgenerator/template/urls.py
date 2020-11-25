from django.urls import path
from template.views import templates, template_detaspec

urlpatterns = [
    path("", templates, name="list.create.templates"),
    path("<int:id>/dataspec", template_detaspec, name='template_dataspec')
]
