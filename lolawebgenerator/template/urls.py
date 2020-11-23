from django.urls import path
from template import views

urlpatterns = [
    path("", views.TemplateView.as_view(), name="list.create.template")
]
