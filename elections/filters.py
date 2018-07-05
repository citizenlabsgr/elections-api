from django_filters import rest_framework as filters

from . import models


DjangoFilterBackend = filters.DjangoFilterBackend


class PrecinctFilter(filters.FilterSet):
    county = filters.NumberFilter()
    jurisdiction = filters.NumberFilter()

    class Meta:
        model = models.Precinct
        fields = [
            'county',
            'county__name',
            'jurisdiction',
            'jurisdiction__name',
            'ward_number',
            'precinct_number',
        ]


class BallotFilter(filters.FilterSet):

    precinct = filters.NumberFilter()

    class Meta:
        model = models.Ballot
        fields = [
            'precinct',
            'precinct__county__name',
            'precinct__jurisdiction__name',
            'precinct__ward_number',
            'precinct__precinct_number',
        ]
