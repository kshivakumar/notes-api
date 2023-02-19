from django.contrib import admin

from .models import Notebook, Page


admin.site.register([Notebook, Page])
