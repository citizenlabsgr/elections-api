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


class VoterFilter(filters.FilterSet):
    first_name = filters.CharFilter(
        name='first_name',
        required=True,
        help_text="Legal first name of potential voter.",
    )
    last_name = filters.CharFilter(
        name='last_name',
        required=True,
        help_text="Last name of potential voter.",
    )
    zip_code = filters.NumberFilter(
        name='zip_code',
        required=True,
        help_text="5-digit zip code of voter's home address.",
    )
    birth_date = filters.DateFilter(
        name='birth_date',
        required=True,
        help_text="Date (YYYY-MM-DD) voter was born.",
    )

    class Meta:
        model = models.Voter
        fields = ['first_name', 'last_name', 'zip_code', 'birth_date']


class ElectionFilter(InitialilzedFilterSet):

    active = filters.BooleanFilter(
        name='active',
        initial=True,
        help_text="Include only recent and upcoming elections. Defaults to true.",
    )

    class Meta:
        model = models.Election
        fields = ['active']


class PrecinctFilter(filters.FilterSet):

    # ID lookup

    county_id = filters.NumberFilter(
        name='county', help_text="Integer value identifying a specific county."
    )
    jurisdiction_id = filters.NumberFilter(
        name='jurisdiction',
        help_text="Integer value identifying a specific jurisdiction.",
    )

    # Value lookup

    county = filters.CharFilter(
        name='county__name', help_text="Name of the county."
    )
    jurisdiction = filters.CharFilter(
        name='jurisdiction__name', help_text="Name of the jurisdiction."
    )
    ward = filters.CharFilter(
        name='ward', help_text="Ward containing the precinct."
    )
    number = filters.CharFilter(
        name='number', help_text="Number of the precinct."
    )

    class Meta:
        model = models.Precinct
        fields = [
            'county_id',
            'jurisdiction_id',
            'county',
            'jurisdiction',
            'ward',
            'number',
        ]


class BallotFilter(InitialilzedFilterSet):

    # Election ID lookup

    election_id = filters.NumberFilter(
        name='election',
        help_text="Integer value identifying a specific election.",
    )

    # Election value lookup

    active_election = filters.BooleanFilter(
        name='election__active',
        initial=True,
        help_text="Include only recent and upcoming elections. Defaults to true.",
    )

    # Precinct ID lookup

    precinct_id = filters.NumberFilter(
        name='precinct',
        help_text="Integer value identifying a specific precinct.",
    )

    # Precinct value lookup

    precinct_county = filters.CharFilter(
        name='precinct__county__name',
        help_text="Name of the precinct's county.",
    )
    precinct_jurisdiction = filters.CharFilter(
        name='precinct__jurisdiction__name',
        help_text="Name of the precinct's jurisdiction.",
    )
    precinct_ward = filters.CharFilter(
        name='precinct__ward', help_text="Ward containing the precinct."
    )
    precinct_number = filters.CharFilter(
        name='precinct__number', help_text="Number of the precinct."
    )

    class Meta:
        model = models.Ballot
        fields = [
            'election_id',
            'precinct_id',
            'precinct_county',
            'precinct_jurisdiction',
            'precinct_ward',
            'precinct_number',
            'active_election',
        ]
