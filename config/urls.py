from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from markdown import markdown
from rest_framework_swagger.views import get_swagger_view


def readme(request):
    path = Path(__file__).parent.parent / "README.md"
    text = ""
    with path.open() as f:
        for line in f:
            if "-- skip --" not in line:
                text += line
    html = markdown(text)
    return HttpResponse(html)


urlpatterns = [
    path("api/", include("elections.urls")),
    path("admin/", admin.site.urls),
    path("grappelli/", include("grappelli.urls")),
    path("docs/", get_swagger_view(title="Michigan Elections API")),
    path("", readme),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls))
    ] + urlpatterns
