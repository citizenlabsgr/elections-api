
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView

from rest_framework_swagger.views import get_swagger_view

from elections import helpers


urlpatterns = [
    path('api/', include('elections.urls')),
    path('admin/', admin.site.urls),
    path('grappelli/', include('grappelli.urls')),
    path('docs/', get_swagger_view(title="Michigan Elections API")),
    path('', TemplateView.as_view(template_name='index.html')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls))
    ] + urlpatterns


if settings.REQUESTS_CACHE_EXPIRE_AFTER:
    helpers.enable_requests_cache(settings.REQUESTS_CACHE_EXPIRE_AFTER)
