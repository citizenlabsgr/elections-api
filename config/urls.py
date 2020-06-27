from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from markdown import markdown


def index(request):
    with Path('README.md').open() as readme:
        text = readme.read()

    text = text.split('<!-- content -->')[1]
    text = text.replace(
        "Michigan.",
        """
        Michigan.
        <br>
        <button class="btn btn-primary mt-3" onclick="location.href='https://share.michiganelections.io'">
            Find Your Ballot
        </button>
        """,
        1,
    )
    text = text.replace('https://michiganelections.io', settings.BASE_URL)
    text = text.replace('>michiganelections.io', f'>{settings.BASE_DOMAIN}')

    html = markdown(
        text, extensions=['pymdownx.magiclink', 'markdown.extensions.tables']
    )
    html = html.replace(' \\', ' \\<br>&nbsp;')

    return render(request, 'index.html', {'body': html})


schema_view = get_schema_view(
    openapi.Info(
        title="Michigan Elections API",
        default_version='0',
        description="Voter registration status and ballots for Michigan.",
    ),
    url=settings.BASE_URL,
)


urlpatterns = [
    path('api/', include('elections.urls')),
    path('admin/', admin.site.urls),
    path('grappelli/', include('grappelli.urls')),
    path('docs/', schema_view.with_ui('swagger')),
    path('', index),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
