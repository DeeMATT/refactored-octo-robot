from django.db import models


class Template(models.Model):
    name = models.CharField(blank=False, null=False, max_length=500)
    url = models.CharField(blank=False, null=False, max_length=500)
