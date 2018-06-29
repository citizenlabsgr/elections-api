from rest_framework import routers

from . import viewsets


router = routers.DefaultRouter()
# router.register(r"users", UserViewSet)
router.register("region-types", viewsets.RegionTypeViewSet)
urlpatterns = router.urls
