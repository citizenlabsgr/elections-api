from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import generics, viewsets
from rest_framework.response import Response

from . import filters, models, serializers


class CacheMixin:
    @method_decorator(cache_page(60 * 60))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)  # type: ignore


class RegistrationViewSet(viewsets.ViewSetMixin, generics.ListAPIView):
    """
    list:
    Return the status of a particular voter's registration.
    """

    queryset = models.Voter.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.VoterFilter
    pagination_class = None

    def list(self, request):  # pylint: disable=arguments-differ
        input_serializer = serializers.VoterSerializer(
            data=request.query_params
        )
        input_serializer.is_valid(raise_exception=True)
        voter = models.Voter(**input_serializer.validated_data)

        registration_status = voter.fetch_registration_status()

        output_serializer = serializers.RegistrationStatusSerializer(
            registration_status, context={'request': request}
        )
        return Response(output_serializer.data)

    @method_decorator(cache_page(60 * 30))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ElectionViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Election](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/election.html)

    list:
    Return all upcoming elections.

    retrieve:
    Return a specific upcoming election.
    """

    http_method_names = ['options', 'get']
    queryset = models.Election.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.ElectionFilter
    serializer_class = serializers.ElectionSerializer


class DistrictCategoryViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: DistrictType](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/enumerations/district_type.html)

    list:
    Return the types of districts, which can filter ballot items.

    retrieve:
    Return a specific type of district, which can filter ballot items.
    """

    http_method_names = ['options', 'get']
    queryset = models.DistrictCategory.objects.all()
    serializer_class = serializers.DistrictCategorySerializer


class DistrictViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Locality](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/locality.html)

    list:
    Return all districts, which can filter ballot items.

    retrieve:
    Return a specific district, which can filter ballot items.
    """

    http_method_names = ['options', 'get']
    queryset = models.District.objects.all().prefetch_related('category')
    serializer_class = serializers.DistrictSerializer


class PrecinctViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Precinct](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/precinct.html)

    list:
    Return all regions which share the same ballot.

    retrieve:
    Return a specific region which shares the same ballot.
    """

    http_method_names = ['options', 'get']
    queryset = models.Precinct.objects.select_related(
        'county', 'jurisdiction'
    ).all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.PrecinctFilter
    serializer_class = serializers.PrecinctSerializer


class BallotViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: BallotStyle](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/ballot_style.html)

    list:
    Return all ballots for upcoming elections.

    retrieve:
    Return a specific ballot for an upcoming election.
    """

    http_method_names = ['options', 'get']
    queryset = models.Ballot.objects.select_related(
        'election', 'precinct', 'precinct__county', 'precinct__jurisdiction'
    ).all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.BallotFilter
    serializer_class = serializers.BallotSerializer


class ProposalViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: BallotMeasureContest](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/ballot_measure_contest.html)

    list:
    Return all proposals for upcoming elections.

    retrieve:
    Return a specific proposal for an upcoming election.
    """

    http_method_names = ['get']
    queryset = models.Proposal.objects.select_related(
        'election', 'district', 'district__category'
    ).all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.ProposalFilter
    serializer_class = serializers.ProposalSerializer


class PartyViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Party](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/party.html)

    list:
    Return all political parties.

    retrieve:
    Return a specific political party.
    """

    http_method_names = ['get']
    queryset = models.Party.objects.all()
    serializer_class = serializers.PartySerializer


class CandidateViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Candidate](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/candidate.html)

    list:
    Return all candidates in an upcoming elections.

    retrieve:
    Return a specific candidate in an upcoming election.
    """

    http_method_names = ['get']
    queryset = models.Candidate.objects.select_related(
        'position', 'party'
    ).all()
    # TODO: Add support for filtering candidates
    # filter_backends = [filters.DjangoFilterBackend]
    # filter_class = filters.CandidateFilter
    serializer_class = serializers.CandidateSerializer


class PositionViewSet(CacheMixin, viewsets.ModelViewSet):
    """
    [VIP 5.1.2: CandidateContest](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/candidate_contest.html)

    list:
    Return all positions for upcoming elections.

    retrieve:
    Return a position proposal for an upcoming election.
    """

    http_method_names = ['get']
    queryset = (
        models.Position.objects.select_related(
            'election', 'district', 'district__category'
        )
        .prefetch_related('candidates', 'candidates__party')
        .all()
    )
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.PositionFilter
    serializer_class = serializers.PositionSerializer
