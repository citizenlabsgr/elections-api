from rest_framework import routers

from . import views


class Index(routers.APIRootView):
    """
    Registration and ballot information for Michigan elections.
    """


class IndexRouter(routers.DefaultRouter):
    APIRootView = Index


router = IndexRouter()

router.register(
    'registrations', views.RegistrationViewSet, base_name='registrations'
)
router.register('district-categories', views.DistrictCategoryViewSet)
router.register('districts', views.DistrictViewSet)

urlpatterns = router.urls
