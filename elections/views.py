
from rest_framework import generics, viewsets
from rest_framework.response import Response

from . import filters, models, serializers


class RegistrationViewSet(viewsets.ViewSetMixin, generics.ListAPIView):
    """Status of a particular voter's registration."""

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

    http_method_names = ['get']
    queryset = models.Election.objects.all()
    serializer_class = serializers.ElectionSerializer


class DistrictCategoryViewSet(viewsets.ModelViewSet):
    """Types of regions that bound ballot items."""

    http_method_names = ['get']
    queryset = models.DistrictCategory.objects.all()
    serializer_class = serializers.DistrictCategorySerializer


class DistrictViewSet(viewsets.ModelViewSet):
    """Districts bound to ballot items."""

    http_method_names = ['get']
    queryset = models.District.objects.all()
    serializer_class = serializers.DistrictSerializer


class PollViewSet(viewsets.ModelViewSet):
    """Regions that share the same ballot."""

    http_method_names = ['get']
    queryset = models.Poll.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.PollFilter
    serializer_class = serializers.PollSerializer


class BallotViewSet(viewsets.ModelViewSet):
    """Ballots bound to individual precincts."""

    http_method_names = ['get']
    queryset = models.Ballot.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filter_class = filters.BallotFilter
    serializer_class = serializers.BallotSerializer
