from django.urls import include, path

from . import v1

urlpatterns = [path("v1", include(v1.urlpatterns))]
