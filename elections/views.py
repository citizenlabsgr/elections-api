import re
from contextlib import suppress

import log
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from . import exceptions, filters, models, serializers


class CachedThrottle(UserRateThrottle):
    """User rate-limiting for non-cached results."""

    scope = "global"

    def get_cache_key(self, request, view):
        return settings.API_CACHE_KEY

    def allow_request(self, request, view):
        if cache.get(self.__class__.get_key(request, view)):
            return True

        return super().allow_request(request, view)

    def parse_rate(self, rate):
        with suppress(KeyError):
            return super().parse_rate(rate)

        # Handle rate formats like "1/5s" or "10/15m"
        match = re.match(r"(\d+)/(\d+)([smhd])", rate)
        if not match:
            raise ValueError(f"Invalid rate format: {rate}")

        num_requests = int(match.group(1))
        time_value = int(match.group(2))
        time_unit = match.group(3)

        # Convert time unit to seconds
        unit_to_seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        duration_in_seconds = time_value * unit_to_seconds[time_unit]

        return num_requests, duration_in_seconds

    @staticmethod
    def get_key(request, view):
        return ":".join(
            (
                str(settings.API_CACHE_KEY),
                view.__class__.__name__,
                request.get_full_path(),
            )
        )


class RegistrationViewSet(viewsets.ViewSetMixin, generics.ListAPIView):
    """
    list:
    Return the status of a particular voter's registration.
    """

    queryset = models.Voter.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = filters.VoterFilter
    serializer_class = serializers.RegistrationSerializer
    pagination_class = None
    throttle_classes = [CachedThrottle]

    def list(self, request):  # pylint: disable=arguments-differ
        if settings.API_CACHE_SECONDS:
            key = CachedThrottle.get_key(request, self)
            if value := cache.get(key):
                return Response(*value)

        input_serializer = serializers.VoterSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        voter = models.Voter(**input_serializer.validated_data)
        registration_status = voter.fetch_registration_status()
        serializer_class = self.get_serializer_class()
        output_serializer = serializer_class(
            registration_status, context={"request": request}
        )

        key = CachedThrottle.get_key(request, self)
        data = output_serializer.data
        cache.set(key, (data, 200), settings.API_CACHE_SECONDS)
        return Response(data)


class StatusViewSet(viewsets.ViewSetMixin, generics.ListAPIView):
    """
    list:
    Return the status of a particular voter's ballot for the latest election.
    """

    queryset = models.Voter.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = filters.VoterFilter
    pagination_class = None
    throttle_classes = [CachedThrottle]

    def list(self, request):  # pylint: disable=arguments-differ
        if settings.API_CACHE_SECONDS:
            key = CachedThrottle.get_key(request, self)
            if value := cache.get(key):
                return Response(*value)

        input_serializer = serializers.VoterSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        voter = models.Voter(**input_serializer.validated_data)
        election = models.Election.objects.filter(active=True).first()
        if election is None:
            election = models.Election.objects.first()
            log.warning(f"No active elections, using latest: {election}")
        try:
            registration_status = voter.fetch_registration_status()
        except exceptions.ServiceUnavailable as e:
            registration_status = models.RegistrationStatus()
            precinct = registration_status.precinct
            data = {
                "id": voter.fingerprint(election, registration_status),
                "message": str(e),
                "election": serializers.MinimalElectionSerializer(election).data,
                "precinct": serializers.MinimalPrecinctSerializer(precinct).data,
                "status": serializers.StatusSerializer(registration_status).data,
                "ballot": serializers.NestedBallotSerializer(None).data,
            }
            status = 202
        else:
            precinct = registration_status.precinct
            ballots = registration_status.ballots
            ballot = ballots[0] if ballots else None
            election = ballot.election if ballot else election
            data = {
                "id": voter.fingerprint(election, registration_status),
                "message": voter.describe(election, registration_status),
                "election": serializers.MinimalElectionSerializer(election).data,
                "precinct": serializers.MinimalPrecinctSerializer(precinct).data,
                "status": serializers.StatusSerializer(registration_status).data,
                "ballot": serializers.NestedBallotSerializer(ballot).data,
            }
            status = 200

        if status < 400:
            key = CachedThrottle.get_key(request, self)
            cache.set(key, (data, status), settings.API_CACHE_SECONDS)
        return Response(data, status)


class ElectionViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: Election](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/election.html)

    list:
    Return all upcoming elections.

    retrieve:
    Return a specific upcoming election.
    """

    http_method_names = ["options", "get"]
    queryset = models.Election.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = filters.ElectionFilter
    serializer_class = serializers.ElectionSerializer


class DistrictCategoryViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: DistrictType](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/enumerations/district_type.html)

    list:
    Return the types of districts, which can filter ballot items.

    retrieve:
    Return a specific type of district, which can filter ballot items.
    """

    http_method_names = ["options", "get"]
    queryset = models.DistrictCategory.objects.all()
    serializer_class = serializers.DistrictCategorySerializer


class DistrictViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: Locality](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/locality.html)

    list:
    Return all districts, which can filter ballot items.

    retrieve:
    Return a specific district, which can filter ballot items.
    """

    http_method_names = ["options", "get"]
    queryset = models.District.objects.all().prefetch_related("category")
    serializer_class = serializers.DistrictSerializer


class PrecinctViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: Precinct](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/precinct.html)

    list:
    Return all regions which share the same ballot.

    retrieve:
    Return a specific region which shares the same ballot.
    """

    http_method_names = ["options", "get"]
    queryset = models.Precinct.objects.select_related("county", "jurisdiction").all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = filters.PrecinctFilter
    serializer_class = serializers.PrecinctSerializer


class BallotViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: BallotStyle](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/ballot_style.html)

    list:
    Return all ballots for upcoming elections.

    retrieve:
    Return a specific ballot for an upcoming election.
    """

    http_method_names = ["options", "get"]
    queryset = models.Ballot.objects.select_related(
        "election", "precinct", "precinct__county", "precinct__jurisdiction", "website"
    ).order_by("-election__date")
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = filters.BallotFilter
    serializer_class = serializers.BallotSerializer

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        instance = get_object_or_404(queryset, **filter_kwargs)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ProposalViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: BallotMeasureContest](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/ballot_measure_contest.html)

    list:
    Return all proposals for upcoming elections.

    retrieve:
    Return a specific proposal for an upcoming election.
    """

    http_method_names = ["get"]
    queryset = (
        models.Proposal.objects.select_related("election", "district__category")
        .order_by("-election__date", "district__category__rank", "name")
        .distinct()
    )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = filters.ProposalFilter
    serializer_class = serializers.ProposalSerializer


class PartyViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: Party](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/party.html)

    list:
    Return all political parties.

    retrieve:
    Return a specific political party.
    """

    http_method_names = ["get"]
    queryset = models.Party.objects.all()
    serializer_class = serializers.PartySerializer


class CandidateViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: Candidate](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/candidate.html)

    list:
    Return all candidates in an upcoming elections.

    retrieve:
    Return a specific candidate in an upcoming election.
    """

    http_method_names = ["get"]
    queryset = models.Candidate.objects.select_related("position", "party").all()
    # TODO: Add support for filtering candidates
    # filter_backends = [filters.DjangoFilterBackend]
    # filterset_class = filters.CandidateFilter
    serializer_class = serializers.CandidateSerializer


class PositionViewSet(viewsets.ModelViewSet):
    """
    [VIP Specification: CandidateContest](https://vip-specification.readthedocs.io/en/latest/built_rst/xml/elements/candidate_contest.html)

    list:
    Return all positions for upcoming elections.

    retrieve:
    Return a position proposal for an upcoming election.
    """

    http_method_names = ["get"]
    queryset = (
        models.Position.objects.select_related("election", "district__category")
        .prefetch_related("candidates__party")
        .order_by("-election__date", "district__category__rank", "name")
        .distinct()
    )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = filters.PositionFilter
    serializer_class = serializers.PositionSerializer

    def get_queryset(self):
        section = self.request.query_params.get("section")
        if section:
            return self.queryset.filter(section__in={section, "Nonpartisan", ""})
        return self.queryset


class GlossaryViewSet(viewsets.ViewSet):
    """
    list:
    Return all glossary terms.
    """

    http_method_names = ["get"]
    serializer_class = serializers.GlossarySerializer

    def list(self, request):
        items: list = []

        items.extend(models.DistrictCategory.objects.all())

        positions: set[str] = set()
        for position in models.Position.objects.all():
            if position.name not in positions:
                positions.add(position.name)
                items.append(position)

        serializer = self.serializer_class(items, many=True)
        return Response(serializer.data)
