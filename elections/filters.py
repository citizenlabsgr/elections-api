from django_filters import rest_framework as filters

from . import models


DjangoFilterBackend = filters.DjangoFilterBackend


class InitialilzedFilterSet(filters.FilterSet):
    def __init__(self, data, *args, **kwargs):
        # pylint: disable=no-member
        if data is not None:
            data = data.copy()
            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')
                if not data.get(name) and initial:
                    data[name] = initial

        super().__init__(data, *args, **kwargs)


class ElectionFilter(InitialilzedFilterSet):

    active = filters.BooleanFilter(name='active', initial=True)

    class Meta:
        model = models.Election
        fields = ['active']


class PrecinctFilter(filters.FilterSet):

    # ID lookup
    county_id = filters.NumberFilter(name='county')
    jurisdiction_id = filters.NumberFilter(name='jurisdiction')

    # Value lookup
    county = filters.CharFilter(name='county__name')
    jurisdiction = filters.CharFilter(name='jurisdiction__name')
    ward = filters.CharFilter(name='ward')
    number = filters.CharFilter(name='number')

    class Meta:
        model = models.Precinct
        fields = [
            # ID lookup
            'county_id',
            'jurisdiction_id',
            # Value lookup
            'county',
            'jurisdiction',
            'ward',
            'number',
        ]


class BallotFilter(InitialilzedFilterSet):

    # Election ID lookup
    election_id = filters.NumberFilter(name='election')

    # Election value lookup
    active_election = filters.BooleanFilter(
        name='election__active', initial=True
    )

    # Precinct ID lookup
    precinct_id = filters.NumberFilter(name='precinct')

    # Precinct value lookup
    precinct_county = filters.CharFilter(name='precinct__county__name')
    precinct_jurisdiction = filters.CharFilter(
        name='precinct__jurisdiction__name'
    )
    precinct_ward = filters.CharFilter(name='precinct__ward')
    precinct_number = filters.CharFilter(name='precinct__number')

    class Meta:
        model = models.Ballot
        fields = [
            # Election ID lookup
            'election_id',
            # Election value lookup
            'active_election',
            # Precinct ID lookup
            'precinct_id',
            # Precinct value lookup
            'precinct_county',
            'precinct_jurisdiction',
            'precinct_ward',
            'precinct_number',
        ]
