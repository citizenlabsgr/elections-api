from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

import grip
from memoize import memoize
from rest_framework_swagger.views import get_swagger_view


TITLE = "Michigan Elections API"


@memoize(60)
def readme(request):
    path = Path(__file__).parent.parent / 'README.md'
    markdown = ''
    with path.open() as f:
        for line in f:
            if '-- skip --' in line:
                continue
            line = line.replace('https://michiganelections.io', '')
            markdown += line
    html = grip.render_page(text=markdown, title=TITLE, render_inline=True)
    return HttpResponse(html)


urlpatterns = [
    path('api/', include('elections.urls')),
    path('admin/', admin.site.urls),
    path('grappelli/', include('grappelli.urls')),
    path('docs/', get_swagger_view(title=TITLE)),
    path('', readme),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls))
    ] + urlpatterns
