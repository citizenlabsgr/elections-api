from rest_framework import routers

from . import views


class Index(routers.APIRootView):
    """
    Registration and ballot information for Michigan elections.
    """


class IndexRouter(routers.DefaultRouter):
    APIRootView = Index


router = IndexRouter()

router.register('registrations', views.RegistrationViewSet, basename='registrations')
router.register('elections', views.ElectionViewSet)

router.register('district-categories', views.DistrictCategoryViewSet)
router.register('districts', views.DistrictViewSet)

router.register('precincts', views.PrecinctViewSet)
router.register('ballots', views.BallotViewSet)

router.register('proposals', views.ProposalViewSet)

router.register('parties', views.PartyViewSet)
router.register('candidates', views.CandidateViewSet)
router.register('positions', views.PositionViewSet)

router.register('glossary', views.GlossaryViewSet, basename='glossary')

urlpatterns = router.urls
