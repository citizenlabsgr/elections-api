import pendulum
from rest_framework import serializers

from . import fields, models


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Voter
        fields = "__all__"


class DistrictCategorySerializer(serializers.HyperlinkedModelSerializer):
    description_edit_url = serializers.SerializerMethodField()

    class Meta:
        model = models.DistrictCategory
        fields = [
            "url",
            "id",
            "name",
            "description",
            "description_edit_url",
        ]

    def get_description_edit_url(self, instance: models.DistrictCategory) -> str:
        category = "districts"
        name = instance.name.replace(" ", "%20")
        return f"https://github.com/citizenlabsgr/elections-api/edit/main/content/{category}/{name}.md"


class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    category = serializers.CharField()

    class Meta:
        model = models.District
        fields = [
            "url",
            "id",
            "category",
            "name",
        ]


class ElectionSerializer(serializers.ModelSerializer):
    date_humanized = serializers.SerializerMethodField()
    proposals_count = serializers.SerializerMethodField()
    positions_count = serializers.SerializerMethodField()

    class Meta:
        model = models.Election
        fields = [
            "url",
            "id",
            "name",
            "date",
            "date_humanized",
            "active",
            "proposals_count",
            "positions_count",
            "reference_url",
        ]

    def get_date_humanized(self, instance: models.Election) -> str:
        dt = pendulum.datetime(
            instance.date.year, instance.date.month, instance.date.day
        )
        return dt.format("dddd, MMMM Do")

    def get_proposals_count(self, instance: models.Election) -> int:
        return instance.proposal_set.count()

    def get_positions_count(self, instance: models.Election) -> int:
        return instance.position_set.count()


class MinimalElectionSerializer(ElectionSerializer):
    class Meta:
        model = models.Election
        fields = [
            "id",
            "name",
            "date",
            "date_humanized",
            "active",
            "reference_url",
        ]


class PrecinctSerializer(serializers.HyperlinkedModelSerializer):
    county = serializers.CharField()
    jurisdiction = serializers.CharField()
    ward = fields.NullCharField()
    number = fields.NullCharField()

    class Meta:
        model = models.Precinct
        fields = [
            "url",
            "id",
            "county",
            "jurisdiction",
            "ward",
            "number",
        ]


class MinimalPrecinctSerializer(serializers.ModelSerializer):
    county = serializers.CharField()
    jurisdiction = serializers.CharField()
    ward = fields.NullCharField()
    number = fields.NullCharField()

    class Meta:
        model = models.Precinct
        fields = [
            "id",
            "county",
            "jurisdiction",
            "ward",
            "number",
        ]


class BallotSerializer(serializers.HyperlinkedModelSerializer):
    election = MinimalElectionSerializer()
    precinct = PrecinctSerializer()

    class Meta:
        model = models.Ballot
        fields = [
            "url",
            "id",
            "election",
            "precinct",
            "mvic_url",
        ]


class MinimalBallotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Ballot
        fields = [
            "url",
            "id",
            "mvic_url",
            "mvic_name",
        ]


class NestedBallotSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = models.Ballot
        fields = [
            "id",
            "mvic_url",
            "items",
        ]

    def get_items(self, instance: models.Ballot) -> int:
        return instance.website.data_count


class ProposalSerializer(serializers.HyperlinkedModelSerializer):
    election = MinimalElectionSerializer()
    district = DistrictSerializer()

    class Meta:
        model = models.Proposal
        fields = [
            "url",
            "id",
            "name",
            "description",
            "reference_url",
            "election",
            "district",
        ]


class PartySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Party
        fields = [
            "url",
            "id",
            "name",
            "color",
        ]


class CandidateSerializer(serializers.HyperlinkedModelSerializer):
    party = PartySerializer()

    class Meta:
        model = models.Candidate
        fields = [
            "url",
            "id",
            "name",
            "description",
            "reference_url",
            "party",
        ]


class PositionSerializer(serializers.HyperlinkedModelSerializer):
    candidates = CandidateSerializer(many=True)
    election = MinimalElectionSerializer()
    district = DistrictSerializer()
    description_edit_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Position
        fields = [
            "url",
            "id",
            "name",
            "description",
            "description_edit_url",
            "reference_url",
            "section",
            "seats",
            "term",
            "candidates",
            "election",
            "district",
        ]

    def get_description_edit_url(self, instance: models.Position) -> str:
        category = "positions"
        name = instance.name.replace(" ", "%20")
        return f"https://github.com/citizenlabsgr/elections-api/edit/main/content/{category}/{name}.md"


class RegistrationSerializer(serializers.HyperlinkedModelSerializer):
    precinct = PrecinctSerializer()
    districts = DistrictSerializer(many=True)
    ballots = MinimalBallotSerializer(many=True)

    class Meta:
        model = models.RegistrationStatus
        fields = [
            "registered",
            "ballot",
            "ballots",
            "absentee",
            "absentee_application_received",
            "absentee_ballot_sent",
            "absentee_ballot_received",
            "polling_location",
            "dropbox_locations",
            "recently_moved",
            "precinct",
            "districts",
        ]


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistrationStatus
        fields = [
            "registered",
            "ballot",
            "absentee",
            "absentee_application_received",
            "absentee_ballot_sent",
            "absentee_ballot_received",
        ]


class GlossarySerializer(serializers.Serializer):  # pylint: disable=abstract-method
    category = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField()
    edit_url = serializers.SerializerMethodField()

    def get_category(self, instance: models.DistrictCategory | models.Position) -> str:
        categories = {
            "DistrictCategory": "districts",
            "Position": "positions",
        }
        model = instance.__class__.__name__
        return categories[model]

    def get_edit_url(self, instance: models.DistrictCategory | models.Position) -> str:
        category = self.get_category(instance)
        name = instance.name.replace(" ", "%20")
        return f"https://github.com/citizenlabsgr/elections-api/edit/main/content/{category}/{name}.md"
