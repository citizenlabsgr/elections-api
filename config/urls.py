from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from markdown import markdown

BALLOT_BUDDIES_HEADING = """

<style>
    a {
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
</style>

<div class="alert alert-secondary d-flex justify-content-between align-items-center mt-lg-5 mt-3 mb-5 gap-4">
    <p class="text-secondary fs-3 my-0 ms-1 d-flex align-items-center">
        <i>Explore elections and help your friends vote.</i>
    </p>
    <button class="btn btn-danger" onclick="location.href='https://app.michiganelections.io/explore/?referrer=api'">
        <span class="d-none d-md-inline">⇨</span> Ballot Buddies App
    </button>
</div>

<h1 class="mt-2 mb-4">Michigan Elections API</h1>

"""


def index(request):
    with Path("README.md").open() as readme:
        text = readme.read()

    text = text.split("<!-- content -->")[1]
    text = BALLOT_BUDDIES_HEADING + text

    text = text.replace("https://michiganelections.io", settings.BASE_URL)
    text = text.replace(">michiganelections.io", f">{settings.BASE_DOMAIN}")

    html = markdown(
        text, extensions=["pymdownx.magiclink", "markdown.extensions.tables"]
    )
    html = html.replace(" \\", " \\<br>&nbsp;")
    html = html.replace("</td>\n<td>", " &nbsp; &nbsp; &nbsp; &nbsp; </td>\n<td>")

    return render(request, "index.html", {"body": html})


schema_view = get_schema_view(
    openapi.Info(
        title="Michigan Elections API",
        default_version="0",
        description="Voter registration status and ballots for Michigan.",
    ),
    url=settings.BASE_URL,
)


urlpatterns = [
    path("api/", include("elections.urls")),
    path("admin/", admin.site.urls),
    path("grappelli/", include("grappelli.urls")),
    path("docs/", schema_view.with_ui("swagger")),
    path("", index),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        path("__reload__/", include("django_browser_reload.urls")),
    ] + urlpatterns
