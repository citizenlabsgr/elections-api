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
router.register('elections', views.ElectionViewSet)
router.register('district-categories', views.DistrictCategoryViewSet)
router.register('districts', views.DistrictViewSet)
router.register('polls', views.PollViewSet)
router.register('ballots', views.BallotViewSet)

urlpatterns = router.urls
