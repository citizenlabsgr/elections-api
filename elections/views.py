
from rest_framework import generics, viewsets
from rest_framework.response import Response

from . import filters, models, serializers


class RegistrationViewSet(viewsets.ViewSetMixin, generics.ListAPIView):
    """
    list:
    Return the status of a particular voter's registration.
    """

    queryset = models.Voter.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_fields = ['first_name', 'last_name', 'zip_code', 'birth_date']
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


class ElectionViewSet(viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Election](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/election.html)

    list:
    Return all upcoming elections.

    retrieve:
    Return a specific upcoming election.
    """

    http_method_names = ['get']
    queryset = models.Election.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.ElectionFilter
    serializer_class = serializers.ElectionSerializer


class DistrictCategoryViewSet(viewsets.ModelViewSet):
    """
    [VIP 5.1.2: DistrictType](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/enumerations/district_type.html)

    list:
    Return the types of districts, which can filter ballot items.

    retrieve:
    Return a specific type of district, which can filter ballot items.
    """

    http_method_names = ['get']
    queryset = models.DistrictCategory.objects.all()
    serializer_class = serializers.DistrictCategorySerializer


class DistrictViewSet(viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Locality](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/locality.html)

    list:
    Return all districts, which can filter ballot items.

    retrieve:
    Return a specific district, which can filter ballot items.
    """

    http_method_names = ['get']
    queryset = models.District.objects.all()
    serializer_class = serializers.DistrictSerializer


class PrecinctViewSet(viewsets.ModelViewSet):
    """
    [VIP 5.1.2: Precinct](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/precinct.html)

    list:
    Return all regions which share the same ballot.

    retrieve:
    Return a specific region which shares the same ballot.
    """

    http_method_names = ['get']
    queryset = models.Precinct.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.PrecinctFilter
    serializer_class = serializers.PrecinctSerializer


class BallotViewSet(viewsets.ModelViewSet):
    """
    [VIP 5.1.2: BallotStyle](https://vip-specification.readthedocs.io/en/vip52/built_rst/xml/elements/ballot_style.html)

    list:
    Return all ballots for upcoming elections.

    retrieve:
    Return a specific ballot for an upcoming election.
    """

    http_method_names = ['get']
    queryset = models.Ballot.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.BallotFilter
    serializer_class = serializers.BallotSerializer
