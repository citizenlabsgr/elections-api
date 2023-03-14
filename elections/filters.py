from django_filters import rest_framework as filters

from . import models

DjangoFilterBackend = filters.DjangoFilterBackend


class InitializedFilterSet(filters.FilterSet):
    def __init__(self, data, *args, **kwargs):
        # pylint: disable=no-member
        if data is not None:
            data = data.copy()
            for name, f in self.base_filters.items():
                initial = f.extra.get("initial")
                if not data.get(name) and initial:
                    data[name] = initial

        super().__init__(data, *args, **kwargs)


class VoterFilter(InitializedFilterSet):
    class Meta:
        model = models.Voter
        fields = ["first_name", "last_name", "zip_code", "birth_date"]

    first_name = filters.CharFilter(
        field_name="first_name",
        required=True,
        help_text="Legal first name of potential voter.",
    )
    last_name = filters.CharFilter(
        field_name="last_name", required=True, help_text="Last name of potential voter."
    )
    zip_code = filters.NumberFilter(
        field_name="zip_code",
        required=True,
        help_text="5-digit zip code of voter's home address.",
    )
    birth_date = filters.DateFilter(
        field_name="birth_date",
        required=True,
        help_text="Date (YYYY-MM-DD) voter was born.",
    )


class ElectionFilter(InitializedFilterSet):
    class Meta:
        model = models.Election
        fields = ["active"]

    active = filters.BooleanFilter(
        field_name="active", help_text="Include only recent and upcoming elections."
    )


class PrecinctFilter(InitializedFilterSet):
    class Meta:
        model = models.Precinct
        fields = [
            "county_id",
            "jurisdiction_id",
            "county",
            "jurisdiction",
            "ward",
            "number",
        ]

    # ID lookup

    county_id = filters.NumberFilter(
        field_name="county",
        label="County ID",
        help_text="Integer value identifying a specific county.",
    )
    jurisdiction_id = filters.NumberFilter(
        field_name="jurisdiction",
        label="Jurisdiction ID",
        help_text="Integer value identifying a specific jurisdiction.",
    )

    # Value lookup

    county = filters.CharFilter(
        field_name="county__name", label="County", help_text="Name of the county."
    )
    jurisdiction = filters.CharFilter(
        field_name="jurisdiction__name",
        label="Jurisdiction",
        help_text="Name of the jurisdiction.",
    )
    ward = filters.CharFilter(
        field_name="ward", help_text="Ward containing the precinct."
    )
    number = filters.CharFilter(
        field_name="number", help_text="Number of the precinct."
    )


class BallotFilter(InitializedFilterSet):
    class Meta:
        model = models.Ballot
        fields = [
            "election_id",
            "precinct_id",
            "precinct_county",
            "precinct_jurisdiction",
            "precinct_ward",
            "precinct_number",
            "active_election",
        ]

    # Election ID lookup

    election_id = filters.NumberFilter(
        field_name="election",
        label="Election ID",
        help_text="Integer value identifying a specific election.",
    )

    # Election value lookup

    active_election = filters.BooleanFilter(
        field_name="election__active",
        initial=True,
        help_text="Include only recent and upcoming elections. Defaults to true.",
    )

    # Precinct ID lookup

    precinct_id = filters.NumberFilter(
        field_name="precinct",
        label="Precinct ID",
        help_text="Integer value identifying a specific precinct.",
    )

    # Precinct value lookup

    precinct_county = filters.CharFilter(
        field_name="precinct__county__name",
        label="County",
        help_text="Name of the precinct's county.",
    )
    precinct_jurisdiction = filters.CharFilter(
        field_name="precinct__jurisdiction__name",
        label="Jurisdiction",
        help_text="Name of the precinct's jurisdiction.",
    )
    precinct_ward = filters.CharFilter(
        field_name="precinct__ward",
        label="Ward",
        help_text="Ward containing the precinct.",
    )
    precinct_number = filters.CharFilter(
        field_name="precinct__number",
        label="Precinct",
        help_text="Number of the precinct.",
    )


class ProposalFilter(InitializedFilterSet):
    class Meta:
        model = models.Proposal
        fields = [
            "election_id",
            "active_election",
            "precinct_id",
            "precinct_county",
            "precinct_jurisdiction",
            "precinct_ward",
            "precinct_number",
            "ballot_id",
        ]

    # Election ID lookup

    election_id = filters.NumberFilter(
        field_name="election",
        label="Election ID",
        help_text="Integer value identifying a specific election.",
    )

    # Election value lookup

    active_election = filters.BooleanFilter(
        field_name="election__active",
        initial=True,
        help_text="Include only recent and upcoming elections. Defaults to true.",
    )

    # Precinct ID lookup

    precinct_id = filters.NumberFilter(
        field_name="precincts",
        label="Precinct ID",
        help_text="Integer value identifying a specific precinct.",
    )

    # Precinct value lookup

    precinct_county = filters.CharFilter(
        field_name="precincts__county__name",
        label="County",
        help_text="Name of the precinct's county.",
    )
    precinct_jurisdiction = filters.CharFilter(
        field_name="precincts__jurisdiction__name",
        label="Jurisdiction",
        help_text="Name of the precinct's jurisdiction.",
    )
    precinct_ward = filters.CharFilter(
        field_name="precincts__ward",
        label="Ward",
        help_text="Ward containing the precinct.",
    )
    precinct_number = filters.CharFilter(
        field_name="precincts__number",
        label="Precinct",
        help_text="Number of the precinct.",
    )

    # Ballot ID lookup

    ballot_id = filters.NumberFilter(
        field_name="ballots",
        label="Ballot ID",
        help_text="Integer value identifying a specific ballot.",
    )


class PositionFilter(InitializedFilterSet):
    class Meta:
        model = models.Position
        fields = [
            "election_id",
            "active_election",
            "precinct_id",
            "precinct_county",
            "precinct_jurisdiction",
            "precinct_ward",
            "precinct_number",
            "ballot_id",
        ]

    # Election ID lookup

    election_id = filters.NumberFilter(
        field_name="election",
        label="Election ID",
        help_text="Integer value identifying a specific election.",
    )

    # Election value lookup

    active_election = filters.BooleanFilter(
        field_name="election__active",
        initial=True,
        help_text="Include only recent and upcoming elections. Defaults to true.",
    )

    # Precinct ID lookup

    precinct_id = filters.NumberFilter(
        field_name="precincts",
        label="Precinct ID",
        help_text="Integer value identifying a specific precinct.",
    )

    # Precinct value lookup

    precinct_county = filters.CharFilter(
        field_name="precincts__county__name",
        label="County",
        help_text="Name of the precinct's county.",
    )
    precinct_jurisdiction = filters.CharFilter(
        field_name="precincts__jurisdiction__name",
        label="Jurisdiction",
        help_text="Name of the precinct's jurisdiction.",
    )
    precinct_ward = filters.CharFilter(
        field_name="precincts__ward",
        label="Ward",
        help_text="Ward containing the precinct.",
    )
    precinct_number = filters.CharFilter(
        field_name="precincts__number",
        label="Precinct",
        help_text="Number of the precinct.",
    )

    # Ballot ID lookup

    ballot_id = filters.NumberFilter(
        field_name="ballots",
        label="Ballot ID",
        help_text="Integer value identifying a specific ballot.",
    )
