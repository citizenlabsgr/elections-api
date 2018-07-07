import os

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import TemplateView

import redis
import requests_cache
from rest_framework_swagger.views import get_swagger_view


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

if settings.EXPIRE_AFTER:
    connection = redis.from_url(os.environ['REDIS_URL'])
    requests_cache.install_cache(
        backend='redis',
        backend_options=dict(connection=connection),
        expire_after=settings.EXPIRE_AFTER,
    )
