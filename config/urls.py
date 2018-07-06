
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import include, path

from rest_framework_swagger.views import get_swagger_view


urlpatterns = [
    path('api/', include('elections.urls')),
    path('admin/', admin.site.urls),
    path('grappelli/', include('grappelli.urls')),
    path('docs/', get_swagger_view(title="Michigan Elections API")),
    path('', serve, kwargs={'path': 'README.html'}),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls))
    ] + urlpatterns
