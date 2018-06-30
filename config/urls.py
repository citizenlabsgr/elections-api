from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from rest_framework_swagger.views import get_swagger_view


schema_view = get_swagger_view(title="Elections API")

urlpatterns = [
    path("api/", include("elections.urls")),
    path("admin/", admin.site.urls),
    path("grappelli/", include("grappelli.urls")),
    path("docs/", schema_view),
    path("", RedirectView.as_view(url="/docs/")),
]
