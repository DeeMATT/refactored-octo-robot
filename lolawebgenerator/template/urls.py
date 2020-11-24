from django.urls import path
from template.views import templates

urlpatterns = [
    path("", templates, name="list.create.templates")
]
